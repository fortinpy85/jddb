/**
 * BulkUpload Component
 * Handles bulk file upload with drag-and-drop, progress tracking, and status management
 */

"use client";

import React, { useState, useCallback, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Progress,
  ProgressIndicator,
  type ProgressStep,
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
  result?: any;
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
  acceptedFileTypes = [".txt", ".doc", ".docx", ".pdf"],
}: BulkUploadProps) {
  const [files, setFiles] = useState<FileUploadStatus[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addToast } = useToast();

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
          errors.push(`${file.name}: Unsupported file type`);
          return;
        }

        // Validate file size
        if (file.size > maxFileSize * 1024 * 1024) {
          errors.push(`${file.name}: File too large (max ${maxFileSize}MB)`);
          return;
        }

        // Check for duplicates
        const isDuplicate = files.some(
          (f) => f.file.name === file.name && f.file.size === file.size,
        );
        if (isDuplicate) {
          errors.push(`${file.name}: File already selected`);
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
          title: "File Selection Issues",
          description: `${errors.length} file(s) couldn't be added. Please check file types and sizes.`,
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
  ): Promise<FileUploadStatus> => {
    try {
      // Update status to uploading
      const updatedFile = {
        ...fileStatus,
        status: "uploading" as const,
        progress: 0,
      };
      updateFileStatus(fileStatus.file, updatedFile);

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        updateFileStatus(fileStatus.file, (prev) => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90),
        }));
      }, 200);

      // Upload file
      const result = await apiClient.uploadFile(fileStatus.file);

      clearInterval(progressInterval);

      // Determine final status based on result
      let finalStatus: FileUploadStatus["status"] = "completed";
      if (
        result.processing_result.processed_content?.processing_errors?.length >
        0
      ) {
        finalStatus = "needs_review";
      }

      const completedFile = {
        ...fileStatus,
        status: finalStatus,
        progress: 100,
        result: result,
      };

      updateFileStatus(fileStatus.file, completedFile);
      return completedFile;
    } catch (error) {
      const failedFile = {
        ...fileStatus,
        status: "failed" as const,
        progress: 0,
        error: error instanceof Error ? error.message : "Upload failed",
      };

      updateFileStatus(fileStatus.file, failedFile);
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

    try {
      const pendingFiles = files.filter(
        (f) => f.status === "pending" || f.status === "failed",
      );

      // Upload files concurrently (max 3 at a time)
      const concurrencyLimit = 3;
      const results: FileUploadStatus[] = [];

      for (let i = 0; i < pendingFiles.length; i += concurrencyLimit) {
        const batch = pendingFiles.slice(i, i + concurrencyLimit);
        const batchPromises = batch.map((file) => uploadSingleFile(file));
        const batchResults = await Promise.all(batchPromises);
        results.push(...batchResults);
      }

      // Show completion notification
      const completed = results.filter((r) => r.status === "completed").length;
      const failed = results.filter((r) => r.status === "failed").length;
      const needsReview = results.filter(
        (r) => r.status === "needs_review",
      ).length;

      if (completed > 0) {
        addToast({
          title: "Upload Complete",
          description: `${completed} file(s) uploaded successfully${failed > 0 ? `, ${failed} failed` : ""}${needsReview > 0 ? `, ${needsReview} need review` : ""}`,
          type: completed === results.length ? "success" : "warning",
        });
      }

      onUploadComplete?.(files);
    } catch (error) {
      console.error("Bulk upload error:", error);
      addToast({
        title: "Bulk Upload Failed",
        description:
          error instanceof Error
            ? error.message
            : "An unexpected error occurred during upload",
        type: "error",
        action: {
          label: "Retry Upload",
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
        return <File className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Bulk File Upload</span>
            {files.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearAllFiles}
                disabled={isUploading}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Clear All
              </Button>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* Drag and Drop Area */}
          <div
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${
                dragActive
                  ? "border-blue-400 bg-blue-50"
                  : "border-gray-300 hover:border-gray-400"
              }
              ${isUploading ? "pointer-events-none opacity-50" : "cursor-pointer"}
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
              title="Select files to upload"
              aria-label="Select files to upload"
            />

            {dragActive ? (
              <div className="text-blue-600">
                <Upload className="w-12 h-12 mx-auto mb-4" />
                <p className="text-lg font-semibold">Drop files here</p>
              </div>
            ) : (
              <div className="text-gray-600">
                <FolderOpen className="w-12 h-12 mx-auto mb-4" />
                <p className="text-lg font-semibold mb-2">
                  Drag and drop files here, or click to select
                </p>
                <p className="text-sm">
                  Supported formats: {acceptedFileTypes.join(", ")} • Max size:{" "}
                  {maxFileSize}MB
                </p>
              </div>
            )}
          </div>

          {/* Upload Button */}
          {files.length > 0 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                {stats.total} files selected
                {stats.completed > 0 && (
                  <span className="ml-2">
                    • {stats.completed} completed
                    {stats.failed > 0 && (
                      <span className="text-red-600">
                        {" "}
                        • {stats.failed} failed
                      </span>
                    )}
                    {stats.needsReview > 0 && (
                      <span className="text-orange-600">
                        {" "}
                        • {stats.needsReview} need review
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
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Upload {stats.pending > 0 ? `(${stats.pending})` : "All"}
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
            <CardTitle>Upload Queue ({files.length})</CardTitle>
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
                            Processed successfully • Job #
                            {
                              fileStatus.result.processing_result?.metadata
                                ?.job_number
                            }
                          </div>
                        )}

                      {/* Review Details */}
                      {fileStatus.result &&
                        fileStatus.status === "needs_review" && (
                          <div className="text-xs text-orange-600 mt-1">
                            Uploaded but needs review •{" "}
                            {
                              fileStatus.result.processing_result
                                ?.processed_content?.processing_errors?.length
                            }{" "}
                            issues
                          </div>
                        )}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Badge className={getStatusColor(fileStatus.status)}>
                      {fileStatus.status.replace("_", " ")}
                    </Badge>

                    {!isUploading && (
                      <>
                        {fileStatus.status === "failed" && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => uploadSingleFile(fileStatus)}
                            title="Retry upload"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeFile(fileStatus.file)}
                          title="Remove file"
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
                  <div className="text-sm text-gray-600">Completed</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-orange-600">
                    {stats.needsReview}
                  </div>
                  <div className="text-sm text-gray-600">Need Review</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-red-600">
                    {stats.failed}
                  </div>
                  <div className="text-sm text-gray-600">Failed</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {stats.processing}
                  </div>
                  <div className="text-sm text-gray-600">Processing</div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
    </div>
  );
}

export default React.memo(BulkUpload);
