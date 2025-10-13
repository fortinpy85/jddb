/**
 * User Preferences Page
 * Allows users to configure application settings and preferences
 */

import React, { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  Settings,
  User,
  Bell,
  Palette,
  Globe,
  Shield,
  Save,
  RotateCcw,
  CheckCircle,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { logger } from "@/utils/logger";

interface UserPreferences {
  // Profile
  display_name: string;
  email: string;

  // Appearance
  theme: "light" | "dark" | "system";
  language: "en" | "fr";

  // Notifications
  enable_notifications: boolean;
  email_notifications: boolean;
  desktop_notifications: boolean;

  // AI Features
  enable_ai_suggestions: boolean;
  auto_analyze_content: boolean;
  suggestion_confidence_threshold: number;

  // Editor
  default_editor_mode: "basic" | "advanced";
  auto_save_interval: number;
  show_line_numbers: boolean;
}

const DEFAULT_PREFERENCES: UserPreferences = {
  display_name: "User",
  email: "", // Will be populated from authenticated user profile
  theme: "system",
  language: "en",
  enable_notifications: true,
  email_notifications: true,
  desktop_notifications: false,
  enable_ai_suggestions: true,
  auto_analyze_content: true,
  suggestion_confidence_threshold: 0.7,
  default_editor_mode: "advanced",
  auto_save_interval: 30,
  show_line_numbers: true,
};

export function UserPreferencesPage() {
  const [preferences, setPreferences] =
    useState<UserPreferences>(DEFAULT_PREFERENCES);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load preferences from backend on mount
  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.getAllPreferences();
      const loadedPrefs = response.preferences;

      // Merge loaded preferences with defaults (in case new fields were added)
      setPreferences({
        ...DEFAULT_PREFERENCES,
        ...loadedPrefs,
      });
    } catch (err) {
      logger.error("Failed to load preferences:", err);
      setError("Failed to load preferences. Using defaults.");
      // Continue with default preferences on error
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof UserPreferences, value: any) => {
    setPreferences((prev) => ({ ...prev, [field]: value }));
    setSaved(false);
    setError(null);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);

    try {
      await apiClient.updatePreferencesBulk(preferences);
      setSaved(true);

      // Clear success message after 3 seconds
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to save preferences";
      setError(errorMessage);
      logger.error("Save preferences error:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setSaving(true);
    setError(null);

    try {
      // Delete all preferences from backend
      await apiClient.resetAllPreferences();

      // Reset to defaults locally
      setPreferences(DEFAULT_PREFERENCES);
      setSaved(false);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to reset preferences";
      setError(errorMessage);
      logger.error("Reset preferences error:", err);
    } finally {
      setSaving(false);
    }
  };

  // Show loading spinner while loading preferences
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <Loader2 className="w-12 h-12 animate-spin mx-auto text-blue-600" />
          <p className="text-gray-600">Loading preferences...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Settings className="w-8 h-8" />
            User Preferences
          </h2>
          <p className="text-gray-600 mt-1">Customize your JDDB experience</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            onClick={handleReset}
            variant="outline"
            size="sm"
            disabled={saving}
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset to Defaults
          </Button>
          <Button onClick={handleSave} size="sm" disabled={saving || saved}>
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : saved ? (
              <>
                <CheckCircle className="w-4 h-4 mr-2" />
                Saved!
              </>
            ) : (
              <>
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-red-800">
              <AlertCircle className="w-5 h-5" />
              <div>
                <div className="font-semibold">Error</div>
                <div className="text-sm">{error}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Success Alert */}
      {saved && (
        <Card className="border-green-200 bg-green-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-green-800">
              <CheckCircle className="w-5 h-5" />
              <div>
                <div className="font-semibold">Success</div>
                <div className="text-sm">Preferences saved successfully!</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Profile Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="w-5 h-5" />
            Profile
          </CardTitle>
          <CardDescription>Manage your profile information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="display_name">Display Name</Label>
            <Input
              id="display_name"
              value={preferences.display_name}
              onChange={(e) => handleChange("display_name", e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={preferences.email}
              onChange={(e) => handleChange("email", e.target.value)}
            />
          </div>
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Palette className="w-5 h-5" />
            Appearance
          </CardTitle>
          <CardDescription>
            Customize the look and feel of the application
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="theme">Theme</Label>
            <Select
              value={preferences.theme}
              onValueChange={(value) => handleChange("theme", value)}
            >
              <SelectTrigger id="theme">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="system">System</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Language */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5" />
            Language & Region
          </CardTitle>
          <CardDescription>Set your preferred language</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="language">Language</Label>
            <Select
              value={preferences.language}
              onValueChange={(value) => handleChange("language", value)}
            >
              <SelectTrigger id="language">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="en">English</SelectItem>
                <SelectItem value="fr">Français</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Notifications
          </CardTitle>
          <CardDescription>
            Manage how you receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable Notifications</Label>
              <div className="text-sm text-gray-500">
                Receive notifications about system events
              </div>
            </div>
            <Switch
              checked={preferences.enable_notifications}
              onCheckedChange={(checked) =>
                handleChange("enable_notifications", checked)
              }
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Email Notifications</Label>
              <div className="text-sm text-gray-500">
                Receive notifications via email
              </div>
            </div>
            <Switch
              checked={preferences.email_notifications}
              onCheckedChange={(checked) =>
                handleChange("email_notifications", checked)
              }
              disabled={!preferences.enable_notifications}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Desktop Notifications</Label>
              <div className="text-sm text-gray-500">
                Show browser notifications
              </div>
            </div>
            <Switch
              checked={preferences.desktop_notifications}
              onCheckedChange={(checked) =>
                handleChange("desktop_notifications", checked)
              }
              disabled={!preferences.enable_notifications}
            />
          </div>
        </CardContent>
      </Card>

      {/* AI Features */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5" />
            AI Features
          </CardTitle>
          <CardDescription>
            Configure AI-powered suggestions and analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Enable AI Suggestions</Label>
              <div className="text-sm text-gray-500">
                Get AI-powered content improvements
              </div>
            </div>
            <Switch
              checked={preferences.enable_ai_suggestions}
              onCheckedChange={(checked) =>
                handleChange("enable_ai_suggestions", checked)
              }
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Auto-Analyze Content</Label>
              <div className="text-sm text-gray-500">
                Automatically analyze content for quality
              </div>
            </div>
            <Switch
              checked={preferences.auto_analyze_content}
              onCheckedChange={(checked) =>
                handleChange("auto_analyze_content", checked)
              }
              disabled={!preferences.enable_ai_suggestions}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confidence_threshold">
              Confidence Threshold:{" "}
              {Math.round(preferences.suggestion_confidence_threshold * 100)}%
            </Label>
            <input
              id="confidence_threshold"
              type="range"
              min="50"
              max="95"
              step="5"
              value={preferences.suggestion_confidence_threshold * 100}
              onChange={(e) =>
                handleChange(
                  "suggestion_confidence_threshold",
                  parseFloat(e.target.value) / 100,
                )
              }
              className="w-full"
              disabled={!preferences.enable_ai_suggestions}
            />
            <div className="text-sm text-gray-500">
              Only show suggestions with{" "}
              {Math.round(preferences.suggestion_confidence_threshold * 100)}%
              or higher confidence
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Editor Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            Editor Settings
          </CardTitle>
          <CardDescription>
            Configure editor behavior and features
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="editor_mode">Default Editor Mode</Label>
            <Select
              value={preferences.default_editor_mode}
              onValueChange={(value) =>
                handleChange("default_editor_mode", value)
              }
            >
              <SelectTrigger id="editor_mode">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="basic">Basic Editor</SelectItem>
                <SelectItem value="advanced">Advanced Editor</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="auto_save">Auto-save Interval (seconds)</Label>
            <Input
              id="auto_save"
              type="number"
              min="10"
              max="300"
              value={preferences.auto_save_interval}
              onChange={(e) =>
                handleChange("auto_save_interval", parseInt(e.target.value))
              }
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Show Line Numbers</Label>
              <div className="text-sm text-gray-500">
                Display line numbers in code editors
              </div>
            </div>
            <Switch
              checked={preferences.show_line_numbers}
              onCheckedChange={(checked) =>
                handleChange("show_line_numbers", checked)
              }
            />
          </div>
        </CardContent>
      </Card>

      {/* Save reminder at bottom */}
      {!saved && !error && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="text-sm text-blue-900">
                Remember to save your changes
              </div>
              <Button onClick={handleSave} size="sm" disabled={saving}>
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
