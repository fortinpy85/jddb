/**
 * BulkUpload Component
 * Handles bulk file upload with drag-and-drop, progress tracking, and status management
 */

"use client";

import React, { useState, useCallback, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Progress,
  // ProgressIndicator,
  // type ProgressStep,
} from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  Upload,
  File,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Trash2,
  FolderOpen,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { formatFileSize, getStatusColor } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";
import { useProgressUtils, ProgressController } from "@/hooks/useProgressToast";
import type { UploadResponse } from "@/types/api";
import { logger } from "@/utils/logger";

interface FileUploadStatus {
  file: File;
  status:
    | "pending"
    | "uploading"
    | "processing"
    | "completed"
    | "failed"
    | "needs_review";
  progress: number;
  error?: string;
  result?: UploadResponse;
}

interface BulkUploadProps {
  onUploadComplete?: (results: FileUploadStatus[]) => void;
  onFilesChange?: (files: FileUploadStatus[]) => void;
  maxFileSize?: number; // in MB
  acceptedFileTypes?: string[];
}

export function BulkUpload({
  onUploadComplete,
  onFilesChange,
  maxFileSize = 50,
  acceptedFileTypes = [".txt", ".doc", ".docx", ".pdf", ".md"],
}: BulkUploadProps) {
  const { t } = useTranslation("upload");
  const [files, setFiles] = useState<FileUploadStatus[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addToast } = useToast();
  const { createUploadProgress, createBatchProgress } = useProgressUtils();

  // Handle file selection
  const handleFileSelect = useCallback(
    (selectedFiles: FileList | null) => {
      if (!selectedFiles) return;

      const newFiles: FileUploadStatus[] = [];
      const errors: string[] = [];

      Array.from(selectedFiles).forEach((file) => {
        // Validate file type
        const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();
        if (!acceptedFileTypes.includes(fileExtension)) {
          errors.push(`${file.name}: ${t("validation.invalidFormat")}`);
          return;
        }

        // Validate file size
        if (file.size > maxFileSize * 1024 * 1024) {
          errors.push(
            `${file.name}: ${t("validation.fileTooBig", { max: maxFileSize })}`,
          );
          return;
        }

        // Check for duplicates
        const isDuplicate = files.some(
          (f) => f.file.name === file.name && f.file.size === file.size,
        );
        if (isDuplicate) {
          errors.push(`${file.name}: ${t("validation.duplicateFile")}`);
          return;
        }

        newFiles.push({
          file,
          status: "pending",
          progress: 0,
        });
      });

      if (errors.length > 0) {
        addToast({
          title: t("messages.fileSelectionIssues"),
          description: t("messages.fileSelectionDescription", {
            count: errors.length,
          }),
          type: "error",
        });
      }

      const updatedFiles = [...files, ...newFiles];
      setFiles(updatedFiles);
      onFilesChange?.(updatedFiles);
    },
    [files, acceptedFileTypes, maxFileSize, onFilesChange],
  );

  // Drag and drop handlers
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelect(e.dataTransfer.files);
      }
    },
    [handleFileSelect],
  );

  // File input change handler
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(e.target.files);
  };

  // Upload single file
  const uploadSingleFile = async (
    fileStatus: FileUploadStatus,
    batchProgress?: ProgressController,
  ): Promise<FileUploadStatus> => {
    let fileProgress: ProgressController | undefined;

    try {
      // Create individual file progress toast if not part of batch
      if (!batchProgress) {
        fileProgress = createUploadProgress(fileStatus.file.name);
      }

      // Update status to uploading
      const updatedFile = {
        ...fileStatus,
        status: "uploading" as const,
        progress: 0,
      };
      updateFileStatus(fileStatus.file, updatedFile);

      // Simulate upload progress with enhanced feedback
      const progressInterval = setInterval(() => {
        updateFileStatus(fileStatus.file, (prev) => {
          const newProgress = Math.min(prev.progress + 10, 90);

          // Update individual file progress toast
          if (fileProgress) {
            if (newProgress < 50) {
              fileProgress.updateProgress(newProgress, t("progress.uploading"));
            } else if (newProgress < 90) {
              fileProgress.updateProgress(
                newProgress,
                t("progress.processing"),
              );
            }
          }

          return {
            ...prev,
            progress: newProgress,
          };
        });
      }, 200);

      // Upload file
      const result = await apiClient.uploadFile(fileStatus.file);

      clearInterval(progressInterval);

      // Determine final status based on result
      let finalStatus: FileUploadStatus["status"] = "completed";
      let statusMessage = t("messages.uploadSuccess");

      if (
        (result.processing_result.processed_content?.processing_errors
          ?.length ?? 0) > 0
      ) {
        finalStatus = "needs_review";
        statusMessage = t("messages.uploadedNeedsReview", {
          count:
            result.processing_result.processed_content?.processing_errors
              ?.length ?? 0,
        });
      }

      const completedFile = {
        ...fileStatus,
        status: finalStatus,
        progress: 100,
        result: result,
      };

      updateFileStatus(fileStatus.file, completedFile);

      // Complete individual file progress toast
      if (fileProgress) {
        if (finalStatus === "completed") {
          fileProgress.complete(statusMessage);
        } else {
          fileProgress.updateProgress(100, statusMessage);
          setTimeout(() => fileProgress?.complete(), 2000);
        }
      }

      return completedFile;
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : t("messages.uploadError", { error: "Unknown error" });

      const failedFile = {
        ...fileStatus,
        status: "failed" as const,
        progress: 0,
        error: errorMessage,
      };

      updateFileStatus(fileStatus.file, failedFile);

      // Show error in individual file progress toast
      if (fileProgress) {
        fileProgress.error(errorMessage);
      }

      return failedFile;
    }
  };

  // Update file status helper
  const updateFileStatus = (
    targetFile: File,
    update: FileUploadStatus | ((prev: FileUploadStatus) => FileUploadStatus),
  ) => {
    setFiles((prevFiles) => {
      const newFiles = prevFiles.map((fileStatus) => {
        if (fileStatus.file === targetFile) {
          return typeof update === "function" ? update(fileStatus) : update;
        }
        return fileStatus;
      });
      onFilesChange?.(newFiles);
      return newFiles;
    });
  };

  // Start bulk upload
  const startBulkUpload = async () => {
    if (files.length === 0 || isUploading) return;

    setIsUploading(true);

    const pendingFiles = files.filter(
      (f) => f.status === "pending" || f.status === "failed",
    );

    // Create batch progress toast
    const batchProgress = createBatchProgress(
      "Bulk Upload",
      pendingFiles.length,
    );

    try {
      // Upload files concurrently (max 3 at a time)
      const concurrencyLimit = 3;
      const results: FileUploadStatus[] = [];
      let completedCount = 0;

      for (let i = 0; i < pendingFiles.length; i += concurrencyLimit) {
        const batch = pendingFiles.slice(i, i + concurrencyLimit);

        // Update batch progress for current batch
        const batchStartProgress = (completedCount / pendingFiles.length) * 100;
        batchProgress.updateProgress(
          batchStartProgress,
          `Processing batch ${Math.floor(i / concurrencyLimit) + 1} of ${Math.ceil(pendingFiles.length / concurrencyLimit)} (${batch.length} files)`,
        );

        const batchPromises = batch.map((file) =>
          uploadSingleFile(file, batchProgress),
        );
        const batchResults = await Promise.all(batchPromises);

        results.push(...batchResults);
        completedCount += batch.length;

        // Update progress after batch completion
        const progressPercent = (completedCount / pendingFiles.length) * 100;
        batchProgress.updateProgress(
          progressPercent,
          `Completed ${completedCount} of ${pendingFiles.length} files`,
        );
      }

      // Calculate final statistics
      const completed = results.filter((r) => r.status === "completed").length;
      const failed = results.filter((r) => r.status === "failed").length;
      const needsReview = results.filter(
        (r) => r.status === "needs_review",
      ).length;

      // Complete batch progress with summary
      let summaryMessage = t("fileList.filesSelected", { count: completed });
      if (failed > 0)
        summaryMessage += `, ${failed} ${t("summary.failed").toLowerCase()}`;
      if (needsReview > 0)
        summaryMessage += `, ${needsReview} ${t("summary.needReview").toLowerCase()}`;

      if (completed > 0) {
        batchProgress.complete(summaryMessage);
      } else {
        batchProgress.error(t("messages.bulkUploadFailed"));
      }

      onUploadComplete?.(files);
    } catch (error) {
      logger.error("Bulk upload error:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : t("messages.uploadError", { error: "Unknown error" });

      batchProgress.error(errorMessage);

      // Show additional error toast with retry action
      addToast({
        title: t("messages.bulkUploadFailed"),
        description: errorMessage,
        type: "error",
        action: {
          label: t("messages.retryUpload"),
          onClick: () => startBulkUpload(),
        },
      });
    } finally {
      setIsUploading(false);
    }
  };

  // Remove file from list
  const removeFile = (targetFile: File) => {
    const updatedFiles = files.filter((f) => f.file !== targetFile);
    setFiles(updatedFiles);
    onFilesChange?.(updatedFiles);
  };

  // Clear all files
  const clearAllFiles = () => {
    setFiles([]);
    onFilesChange?.([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  // Get upload statistics
  const getUploadStats = () => {
    const total = files.length;
    const completed = files.filter((f) => f.status === "completed").length;
    const failed = files.filter((f) => f.status === "failed").length;
    const needsReview = files.filter((f) => f.status === "needs_review").length;
    const processing = files.filter(
      (f) => f.status === "uploading" || f.status === "processing",
    ).length;
    const pending = files.filter((f) => f.status === "pending").length;

    return { total, completed, failed, needsReview, processing, pending };
  };

  const stats = getUploadStats();

  // Status icon component
  const StatusIcon = ({ status }: { status: FileUploadStatus["status"] }) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-600" />;
      case "needs_review":
        return <AlertCircle className="w-4 h-4 text-orange-600" />;
      case "uploading":
      case "processing":
        return <RefreshCw className="w-4 h-4 text-blue-600 animate-spin" />;
      default:
        return <File className="w-4 h-4 text-gray-600 dark:text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>{t("title")}</span>
            {files.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearAllFiles}
                disabled={isUploading}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                {t("actions.clearAll")}
              </Button>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Drag and Drop Area */}
          <div
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200
              ${
                dragActive
                  ? "border-blue-500 bg-blue-50 border-solid shadow-lg scale-[1.02]"
                  : "border-gray-500 dark:border-gray-600 hover:border-blue-400 hover:bg-gray-50"
              }
              ${isUploading ? "pointer-events-none opacity-50" : "cursor-pointer hover:shadow-md"}
            `}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={acceptedFileTypes.join(",")}
              onChange={handleFileInputChange}
              className="hidden"
              disabled={isUploading}
              title={t("accessibility.selectFiles")}
              aria-label={t("accessibility.selectFiles")}
            />

            {dragActive ? (
              <div className="text-blue-600">
                <Upload className="w-16 h-16 mx-auto mb-4 animate-bounce" />
                <p className="text-xl font-semibold">
                  {t("dropzone.dropHere")}
                </p>
                <p className="text-sm mt-2 opacity-75">
                  {t("dropzone.releaseToUpload")}
                </p>
              </div>
            ) : (
              <div className="text-gray-700">
                <FolderOpen className="w-16 h-16 mx-auto mb-4 text-gray-600 dark:text-gray-400" />
                <p className="text-xl font-semibold mb-2">
                  {t("dropzone.title")}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {t("dropzone.supportedFormats")}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  {t("dropzone.maxSize", { size: maxFileSize })}
                </p>
              </div>
            )}
          </div>

          {/* Upload Button */}
          {files.length > 0 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {t("fileList.filesSelected", { count: stats.total })}
                {stats.completed > 0 && (
                  <span className="ml-2">
                    • {stats.completed} {t("summary.completed").toLowerCase()}
                    {stats.failed > 0 && (
                      <span className="text-red-600">
                        {" "}
                        • {stats.failed} {t("summary.failed").toLowerCase()}
                      </span>
                    )}
                    {stats.needsReview > 0 && (
                      <span className="text-orange-600">
                        {" "}
                        • {stats.needsReview}{" "}
                        {t("summary.needReview").toLowerCase()}
                      </span>
                    )}
                  </span>
                )}
              </div>

              <Button
                onClick={startBulkUpload}
                disabled={isUploading || stats.pending === 0}
                className="min-w-32"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    {t("status.uploading")}...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    {t("actions.upload")}{" "}
                    {stats.pending > 0
                      ? `(${stats.pending})`
                      : t("actions.uploadAll")}
                  </>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>
              {t("fileList.title")} ({files.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {files.map((fileStatus, index) => (
                <div
                  key={`${fileStatus.file.name}-${index}`}
                  className="flex items-center justify-between p-3 border rounded-lg"
                >
                  <div className="flex items-center space-x-3 flex-1">
                    <StatusIcon status={fileStatus.status} />

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {fileStatus.file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(fileStatus.file.size)}
                      </p>

                      {/* Progress Bar */}
                      {(fileStatus.status === "uploading" ||
                        fileStatus.status === "processing") && (
                        <div className="mt-2">
                          <Progress
                            value={fileStatus.progress}
                            className="h-1"
                          />
                        </div>
                      )}

                      {/* Error Message */}
                      {fileStatus.error && (
                        <p className="text-xs text-red-600 mt-1">
                          {fileStatus.error}
                        </p>
                      )}

                      {/* Success Details */}
                      {fileStatus.result &&
                        fileStatus.status === "completed" && (
                          <div className="text-xs text-green-600 mt-1">
                            {t("messages.processedSuccessfully", {
                              jobNumber:
                                fileStatus.result.processing_result
                                  ?.file_metadata?.job_number,
                            })}
                          </div>
                        )}

                      {/* Review Details */}
                      {fileStatus.result &&
                        fileStatus.status === "needs_review" && (
                          <div className="text-xs text-orange-600 mt-1">
                            {t("messages.uploadedNeedsReview", {
                              count:
                                fileStatus.result.processing_result
                                  ?.processed_content?.processing_errors
                                  ?.length,
                            })}
                          </div>
                        )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(fileStatus.status)}>
                      {t(
                        `status.${fileStatus.status === "needs_review" ? "needsReview" : fileStatus.status}`,
                      )}
                    </Badge>

                    {!isUploading && (
                      <>
                        {fileStatus.status === "failed" && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => uploadSingleFile(fileStatus)}
                            title={t("accessibility.retryUpload")}
                          >
                            <RefreshCw className="w-4 h-4" />
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeFile(fileStatus.file)}
                          title={t("accessibility.removeFile")}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upload Summary */}
      {files.length > 0 &&
        (stats.completed > 0 || stats.failed > 0 || stats.needsReview > 0) && (
          <Card>
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {stats.completed}
                  </div>
                  <div className="text-sm text-gray-600">
                    {t("summary.completed")}
                  </div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-orange-600">
                    {stats.needsReview}
                  </div>
                  <div className="text-sm text-gray-600">
                    {t("summary.needReview")}
                  </div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">
                    {stats.failed}
                  </div>
                  <div className="text-sm text-gray-600">
                    {t("summary.failed")}
                  </div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {stats.processing}
                  </div>
                  <div className="text-sm text-gray-600">
                    {t("summary.processing")}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
    </div>
  );
}

export default React.memo(BulkUpload);
