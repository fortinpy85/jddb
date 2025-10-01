/**
 * Keyboard Shortcuts Help Modal
 * Displays available keyboard shortcuts organized by category
 */

"use client";

import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Keyboard, Navigation, Search, Zap, HelpCircle } from "lucide-react";
import { KeyboardShortcut, formatShortcut } from "@/hooks/useKeyboardShortcuts";

interface KeyboardShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
  shortcuts: KeyboardShortcut[];
}

const CATEGORY_INFO = {
  navigation: {
    title: "Navigation",
    icon: Navigation,
    description: "Move between different sections",
    color: "bg-blue-500",
  },
  search: {
    title: "Search",
    icon: Search,
    description: "Search and filtering shortcuts",
    color: "bg-green-500",
  },
  actions: {
    title: "Actions",
    icon: Zap,
    description: "Quick actions and operations",
    color: "bg-purple-500",
  },
  editing: {
    title: "Editing",
    icon: HelpCircle,
    description: "Content editing shortcuts",
    color: "bg-orange-500",
  },
};

export function KeyboardShortcutsModal({
  isOpen,
  onClose,
  shortcuts,
}: KeyboardShortcutsModalProps) {
  // Group shortcuts by category
  const groupedShortcuts = shortcuts.reduce(
    (acc, shortcut) => {
      if (!acc[shortcut.category]) {
        acc[shortcut.category] = [];
      }
      acc[shortcut.category].push(shortcut);
      return acc;
    },
    {} as Record<string, KeyboardShortcut[]>,
  );

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent
        className="max-w-4xl max-h-[80vh] overflow-y-auto"
        data-testid="keyboard-shortcuts-modal"
      >
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <Keyboard className="w-5 h-5" />
            <span>Keyboard Shortcuts</span>
          </DialogTitle>
          <DialogDescription>
            Use these shortcuts to navigate and work more efficiently in JDDB
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          {Object.entries(groupedShortcuts).map(
            ([category, categoryShortcuts]) => {
              const categoryInfo =
                CATEGORY_INFO[category as keyof typeof CATEGORY_INFO];
              if (!categoryInfo) return null;

              const Icon = categoryInfo.icon;

              return (
                <Card key={category} className="h-fit">
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center space-x-2 text-sm">
                      <div
                        className={`w-2 h-2 rounded-full ${categoryInfo.color}`}
                      />
                      <Icon className="w-4 h-4" />
                      <span>{categoryInfo.title}</span>
                    </CardTitle>
                    <p className="text-xs text-muted-foreground">
                      {categoryInfo.description}
                    </p>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {categoryShortcuts.map((shortcut, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between py-2 px-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
                      >
                        <span className="text-sm text-foreground font-medium">
                          {shortcut.description}
                        </span>
                        <Badge
                          variant="outline"
                          className="font-mono text-xs px-2 py-1 bg-background"
                        >
                          {formatShortcut(shortcut)}
                        </Badge>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              );
            },
          )}
        </div>

        <div className="mt-6 p-4 bg-muted/30 rounded-lg">
          <div className="flex items-start space-x-2">
            <HelpCircle className="w-4 h-4 mt-0.5 text-muted-foreground" />
            <div className="space-y-1">
              <p className="text-sm font-medium">Tips</p>
              <ul className="text-xs text-muted-foreground space-y-1">
                <li>
                  • Shortcuts work from anywhere except when typing in input
                  fields
                </li>
                <li>
                  • Press{" "}
                  <Badge variant="outline" className="text-xs px-1 py-0">
                    ?
                  </Badge>{" "}
                  or{" "}
                  <Badge variant="outline" className="text-xs px-1 py-0">
                    Ctrl+H
                  </Badge>{" "}
                  to show this help anytime
                </li>
                <li>
                  • Use{" "}
                  <Badge variant="outline" className="text-xs px-1 py-0">
                    /
                  </Badge>{" "}
                  or{" "}
                  <Badge variant="outline" className="text-xs px-1 py-0">
                    Ctrl+K
                  </Badge>{" "}
                  to quickly focus search
                </li>
              </ul>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Hook for managing keyboard shortcuts modal
 */
export function useKeyboardShortcutsModal() {
  const [isOpen, setIsOpen] = React.useState(false);

  const openModal = React.useCallback(() => setIsOpen(true), []);
  const closeModal = React.useCallback(() => setIsOpen(false), []);

  return {
    isOpen,
    openModal,
    closeModal,
    KeyboardShortcutsModal: React.useCallback(
      (props: Omit<KeyboardShortcutsModalProps, "isOpen" | "onClose">) => (
        <KeyboardShortcutsModal
          {...props}
          isOpen={isOpen}
          onClose={closeModal}
        />
      ),
      [isOpen, closeModal],
    ),
  };
}
