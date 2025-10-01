/**
 * Enhanced Form Components
 * Modern form elements with improved UX and validation
 */

"use client";

import React, { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  Search,
  Filter,
  X,
  ChevronDown,
  Check,
  Upload,
  FileText,
  AlertCircle,
  Eye,
  EyeOff,
} from "lucide-react";

/**
 * Enhanced Search Input
 * Search input with filters and suggestions
 */
interface EnhancedSearchProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSearch?: (value: string) => void;
  suggestions?: string[];
  filters?: Array<{
    id: string;
    label: string;
    icon?: React.ComponentType<{ className?: string }>;
    count?: number;
  }>;
  activeFilters?: string[];
  onFilterChange?: (filters: string[]) => void;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function EnhancedSearch({
  placeholder = "Search...",
  value = "",
  onChange,
  onSearch,
  suggestions = [],
  filters = [],
  activeFilters = [],
  onFilterChange,
  className,
  size = "md",
}: EnhancedSearchProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange?.(newValue);
    setShowSuggestions(newValue.length > 0 && suggestions.length > 0);
  };

  const handleSuggestionClick = (suggestion: string) => {
    onChange?.(suggestion);
    setShowSuggestions(false);
    onSearch?.(suggestion);
  };

  const handleFilterToggle = (filterId: string) => {
    const newFilters = activeFilters.includes(filterId)
      ? activeFilters.filter((f) => f !== filterId)
      : [...activeFilters, filterId];
    onFilterChange?.(newFilters);
  };

  const clearSearch = () => {
    onChange?.("");
    inputRef.current?.focus();
  };

  const sizeClasses = {
    sm: "h-8 text-sm",
    md: "h-10 text-sm",
    lg: "h-12 text-base",
  };

  return (
    <div className={cn("relative", className)}>
      {/* Main Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          ref={inputRef}
          type="search"
          placeholder={placeholder}
          value={value}
          onChange={handleInputChange}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              onSearch?.(value);
              setShowSuggestions(false);
            }
          }}
          className={cn(
            "pl-10 pr-20 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700",
            "focus:border-blue-500 focus:ring-blue-500",
            sizeClasses[size],
          )}
        />

        {/* Clear and Filter Buttons */}
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
          {value && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearSearch}
              className="h-6 w-6 p-0 hover:bg-slate-100 dark:hover:bg-slate-700"
            >
              <X className="w-3 h-3" />
            </Button>
          )}
          {filters.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className={cn(
                "h-6 w-6 p-0 hover:bg-slate-100 dark:hover:bg-slate-700",
                activeFilters.length > 0 && "text-blue-600 bg-blue-50",
              )}
            >
              <Filter className="w-3 h-3" />
              {activeFilters.length > 0 && (
                <Badge className="absolute -top-1 -right-1 h-4 w-4 p-0 text-xs">
                  {activeFilters.length}
                </Badge>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Suggestions Dropdown */}
      {showSuggestions && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-50 max-h-48 overflow-y-auto">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSuggestionClick(suggestion)}
              className="w-full px-4 py-2 text-left hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors duration-150"
            >
              <span className="text-sm text-slate-700 dark:text-slate-300">
                {suggestion}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Filters Panel */}
      {showFilters && filters.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg z-50 p-4">
          <h4 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-3">
            Filter Results
          </h4>
          <div className="space-y-2">
            {filters.map((filter) => {
              const isActive = activeFilters.includes(filter.id);
              const Icon = filter.icon;

              return (
                <button
                  key={filter.id}
                  onClick={() => handleFilterToggle(filter.id)}
                  className={cn(
                    "w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors duration-150",
                    isActive
                      ? "bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400"
                      : "hover:bg-slate-50 dark:hover:bg-slate-700",
                  )}
                >
                  <div className="flex items-center space-x-2">
                    {Icon && <Icon className="w-4 h-4" />}
                    <span className="text-sm font-medium">{filter.label}</span>
                    {filter.count !== undefined && (
                      <Badge variant="secondary" className="text-xs">
                        {filter.count}
                      </Badge>
                    )}
                  </div>
                  {isActive && <Check className="w-4 h-4" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Enhanced File Upload
 * Drag-and-drop file upload with preview and validation
 */
interface EnhancedFileUploadProps {
  accept?: string;
  multiple?: boolean;
  maxSize?: number; // in MB
  maxFiles?: number;
  onFilesChange?: (files: File[]) => void;
  preview?: boolean;
  className?: string;
}

export function EnhancedFileUpload({
  accept = "*/*",
  multiple = false,
  maxSize = 10,
  maxFiles = 5,
  onFilesChange,
  preview = true,
  className,
}: EnhancedFileUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (file.size > maxSize * 1024 * 1024) {
      return `File ${file.name} is too large. Maximum size is ${maxSize}MB.`;
    }
    return null;
  };

  const handleFiles = (newFiles: FileList | null) => {
    if (!newFiles) return;

    const fileArray = Array.from(newFiles);
    const validFiles: File[] = [];
    const newErrors: string[] = [];

    // Validate each file
    fileArray.forEach((file) => {
      const error = validateFile(file);
      if (error) {
        newErrors.push(error);
      } else {
        validFiles.push(file);
      }
    });

    // Check total file count
    const totalFiles = files.length + validFiles.length;
    if (totalFiles > maxFiles) {
      newErrors.push(`Too many files. Maximum is ${maxFiles} files.`);
      return;
    }

    const updatedFiles = multiple ? [...files, ...validFiles] : validFiles;
    setFiles(updatedFiles);
    setErrors(newErrors);
    onFilesChange?.(updatedFiles);
  };

  const removeFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index);
    setFiles(updatedFiles);
    onFilesChange?.(updatedFiles);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className={cn("space-y-4", className)}>
      {/* Upload Area */}
      <div
        className={cn(
          "relative border-2 border-dashed rounded-lg p-6 text-center transition-colors duration-200",
          dragActive
            ? "border-blue-400 bg-blue-50 dark:bg-blue-900/20"
            : "border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500",
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={(e) => handleFiles(e.target.files)}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />

        <Upload className="mx-auto h-12 w-12 text-slate-400 mb-4" />
        <p className="text-lg font-medium text-slate-700 dark:text-slate-300 mb-2">
          Drop files here or click to browse
        </p>
        <p className="text-sm text-slate-500 dark:text-slate-400">
          {accept !== "*/*" && `Accepts: ${accept} • `}
          Max size: {maxSize}MB
          {multiple && ` • Max files: ${maxFiles}`}
        </p>
      </div>

      {/* Error Messages */}
      {errors.length > 0 && (
        <div className="space-y-2">
          {errors.map((error, index) => (
            <div
              key={index}
              className="flex items-center space-x-2 text-sm text-red-600 dark:text-red-400"
            >
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          ))}
        </div>
      )}

      {/* File Preview */}
      {preview && files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300">
            Selected Files ({files.length})
          </h4>
          <div className="space-y-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <FileText className="w-5 h-5 text-slate-500" />
                  <div>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      {file.name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeFile(index)}
                  className="h-8 w-8 p-0 text-slate-400 hover:text-red-500"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Enhanced Input with Validation
 * Input field with built-in validation and feedback
 */
interface EnhancedInputProps {
  label?: string;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  type?: "text" | "email" | "password" | "number" | "tel" | "url";
  required?: boolean;
  validation?: {
    required?: boolean;
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    custom?: (value: string) => string | null;
  };
  helpText?: string;
  icon?: React.ComponentType<{ className?: string }>;
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function EnhancedInput({
  label,
  placeholder,
  value = "",
  onChange,
  type = "text",
  required = false,
  validation,
  helpText,
  icon: Icon,
  className,
  size = "md",
}: EnhancedInputProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  const validateValue = (val: string) => {
    if (!validation) return null;

    if (validation.required && !val.trim()) {
      return "This field is required";
    }

    if (validation.minLength && val.length < validation.minLength) {
      return `Minimum length is ${validation.minLength} characters`;
    }

    if (validation.maxLength && val.length > validation.maxLength) {
      return `Maximum length is ${validation.maxLength} characters`;
    }

    if (validation.pattern && !validation.pattern.test(val)) {
      return "Invalid format";
    }

    if (validation.custom) {
      return validation.custom(val);
    }

    return null;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    onChange?.(newValue);

    if (touched) {
      setError(validateValue(newValue));
    }
  };

  const handleBlur = () => {
    setTouched(true);
    setError(validateValue(value));
  };

  const inputType = type === "password" && showPassword ? "text" : type;
  const hasError = touched && error;

  const sizeClasses = {
    sm: "h-8 text-sm",
    md: "h-10 text-sm",
    lg: "h-12 text-base",
  };

  return (
    <div className={cn("space-y-2", className)}>
      {/* Label */}
      {label && (
        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {/* Input Container */}
      <div className="relative">
        {Icon && (
          <Icon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
        )}
        <Input
          type={inputType}
          placeholder={placeholder}
          value={value}
          onChange={handleChange}
          onBlur={handleBlur}
          className={cn(
            Icon && "pl-10",
            type === "password" && "pr-10",
            hasError &&
              "border-red-500 focus:border-red-500 focus:ring-red-500",
            sizeClasses[size],
          )}
        />
        {type === "password" && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
          >
            {showPassword ? (
              <EyeOff className="w-4 h-4" />
            ) : (
              <Eye className="w-4 h-4" />
            )}
          </Button>
        )}
      </div>

      {/* Help Text or Error */}
      {(helpText || hasError) && (
        <div className="flex items-start space-x-1">
          {hasError && (
            <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
          )}
          <p
            className={cn(
              "text-xs",
              hasError
                ? "text-red-600 dark:text-red-400"
                : "text-slate-500 dark:text-slate-400",
            )}
          >
            {hasError ? error : helpText}
          </p>
        </div>
      )}
    </div>
  );
}
