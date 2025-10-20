"use client";

import * as React from "react";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { Check, ChevronRight, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

const DropdownMenu = DropdownMenuPrimitive.Root;

const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger;

const DropdownMenuGroup = DropdownMenuPrimitive.Group;

const DropdownMenuPortal = DropdownMenuPrimitive.Portal;

const DropdownMenuSub = DropdownMenuPrimitive.Sub;

const DropdownMenuRadioGroup = DropdownMenuPrimitive.RadioGroup;

const DropdownMenuSubTrigger = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.SubTrigger>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.SubTrigger> & {
    inset?: boolean;
  }
>(({ className, inset, children, ...props }, ref) => (
  <DropdownMenuPrimitive.SubTrigger
    ref={ref}
    className={cn(
      "flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none focus:bg-accent data-[state=open]:bg-accent",
      inset && "pl-8",
      className,
    )}
    {...props}
  >
    {children}
    <ChevronRight className="ml-auto h-4 w-4" />
  </DropdownMenuPrimitive.SubTrigger>
));
DropdownMenuSubTrigger.displayName =
  DropdownMenuPrimitive.SubTrigger.displayName;

const DropdownMenuSubContent = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.SubContent>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.SubContent>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.SubContent
    ref={ref}
    className={cn(
      "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-lg data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2",
      className,
    )}
    {...props}
  />
));
DropdownMenuSubContent.displayName =
  DropdownMenuPrimitive.SubContent.displayName;

const DropdownMenuContent = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(({ className, sideOffset = 4, style, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        "z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 opacity-100",
        className,
      )}
      style={{
        ...style,
        // Ensure opaque background
        opacity: 1,
        backgroundColor: "var(--popover)",
      }}
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
));
DropdownMenuContent.displayName = DropdownMenuPrimitive.Content.displayName;

const DropdownMenuItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item> & {
    inset?: boolean;
  }
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      inset && "pl-8",
      className,
    )}
    {...props}
  />
));
DropdownMenuItem.displayName = DropdownMenuPrimitive.Item.displayName;

const DropdownMenuCheckboxItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.CheckboxItem>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.CheckboxItem>
>(({ className, children, checked, ...props }, ref) => (
  <DropdownMenuPrimitive.CheckboxItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className,
    )}
    checked={checked}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <Check className="h-4 w-4" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.CheckboxItem>
));
DropdownMenuCheckboxItem.displayName =
  DropdownMenuPrimitive.CheckboxItem.displayName;

const DropdownMenuRadioItem = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.RadioItem>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.RadioItem>
>(({ className, children, ...props }, ref) => (
  <DropdownMenuPrimitive.RadioItem
    ref={ref}
    className={cn(
      "relative flex cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
      className,
    )}
    {...props}
  >
    <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
      <DropdownMenuPrimitive.ItemIndicator>
        <Circle className="h-2 w-2 fill-current" />
      </DropdownMenuPrimitive.ItemIndicator>
    </span>
    {children}
  </DropdownMenuPrimitive.RadioItem>
));
DropdownMenuRadioItem.displayName = DropdownMenuPrimitive.RadioItem.displayName;

const DropdownMenuLabel = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Label>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Label> & {
    inset?: boolean;
  }
>(({ className, inset, ...props }, ref) => (
  <DropdownMenuPrimitive.Label
    ref={ref}
    className={cn(
      "px-2 py-1.5 text-sm font-semibold",
      inset && "pl-8",
      className,
    )}
    {...props}
  />
));
DropdownMenuLabel.displayName = DropdownMenuPrimitive.Label.displayName;

const DropdownMenuSeparator = React.forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Separator
    ref={ref}
    className={cn("-mx-1 my-1 h-px bg-muted", className)}
    {...props}
  />
));
DropdownMenuSeparator.displayName = DropdownMenuPrimitive.Separator.displayName;

const DropdownMenuShortcut = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) => {
  return (
    <span
      className={cn("ml-auto text-xs tracking-widest opacity-60", className)}
      {...props}
    />
  );
};
DropdownMenuShortcut.displayName = "DropdownMenuShortcut";

// ContextualMenu functionality
import { Button } from "@/components/ui/button";
import {
  MoreHorizontal,
  MoreVertical,
  Eye,
  Edit,
  Download,
  Share2,
  Copy,
  Trash2,
  Star,
  Archive,
  GitCompare,
  ExternalLink,
  FileText,
  Settings,
} from "lucide-react";

export interface ContextualAction {
  id: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  shortcut?: string;
  disabled?: boolean;
  destructive?: boolean;
  href?: string;
  external?: boolean;
  onClick?: () => void;
}

export interface ContextualMenuGroup {
  label?: string;
  actions: ContextualAction[];
}

interface ContextualMenuProps {
  trigger?: React.ReactNode;
  groups: ContextualMenuGroup[];
  align?: "start" | "center" | "end";
  side?: "top" | "right" | "bottom" | "left";
  className?: string;
  triggerClassName?: string;
  variant?: "dots" | "button" | "custom";
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
}

function ContextualMenu({
  trigger,
  groups,
  align = "end",
  side = "bottom",
  className,
  triggerClassName,
  variant = "dots",
  size = "md",
  disabled = false,
}: ContextualMenuProps) {
  const sizeClasses = {
    sm: "h-6 w-6",
    md: "h-8 w-8",
    lg: "h-10 w-10",
  };

  const iconSizes = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5",
  };

  const renderTrigger = () => {
    if (trigger) return trigger;

    if (variant === "button") {
      return (
        <Button
          variant="outline"
          size={size === "md" ? "default" : size}
          disabled={disabled}
          className={cn(triggerClassName)}
        >
          <MoreHorizontal className={iconSizes[size]} />
        </Button>
      );
    }

    return (
      <Button
        variant="ghost"
        size="icon"
        disabled={disabled}
        className={cn(sizeClasses[size], triggerClassName)}
      >
        {variant === "dots" ? (
          <MoreVertical className={iconSizes[size]} />
        ) : (
          <MoreHorizontal className={iconSizes[size]} />
        )}
      </Button>
    );
  };

  const handleAction = (action: ContextualAction) => {
    if (action.disabled) return;

    if (action.href) {
      if (action.external) {
        window.open(action.href, "_blank", "noopener,noreferrer");
      } else {
        window.location.href = action.href;
      }
    } else if (action.onClick) {
      action.onClick();
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild disabled={disabled}>
        {renderTrigger()}
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align={align}
        side={side}
        className={cn("w-56", className)}
      >
        {groups.map((group, groupIndex) => (
          <React.Fragment key={groupIndex}>
            {group.label && (
              <DropdownMenuLabel>{group.label}</DropdownMenuLabel>
            )}
            {group.actions.map((action) => {
              const Icon = action.icon;

              return (
                <DropdownMenuItem
                  key={action.id}
                  disabled={action.disabled}
                  className={cn(
                    "cursor-pointer",
                    action.destructive && "text-red-600 focus:text-red-600",
                    action.disabled && "opacity-50 cursor-not-allowed",
                  )}
                  onClick={() => handleAction(action)}
                >
                  {Icon && <Icon className="mr-2 h-4 w-4" />}
                  <span className="flex-1">{action.label}</span>
                  {action.external && <ExternalLink className="ml-2 h-3 w-3" />}
                  {action.shortcut && (
                    <DropdownMenuShortcut>
                      {action.shortcut}
                    </DropdownMenuShortcut>
                  )}
                </DropdownMenuItem>
              );
            })}
            {groupIndex < groups.length - 1 && <DropdownMenuSeparator />}
          </React.Fragment>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// Predefined action configurations for common use cases
const COMMON_ACTIONS = {
  view: (onClick: () => void): ContextualAction => ({
    id: "view",
    label: "View Details",
    icon: Eye,
    shortcut: "⌘↵",
    onClick,
  }),

  edit: (onClick: () => void): ContextualAction => ({
    id: "edit",
    label: "Edit",
    icon: Edit,
    shortcut: "⌘E",
    onClick,
  }),

  download: (onClick: () => void): ContextualAction => ({
    id: "download",
    label: "Download",
    icon: Download,
    shortcut: "⌘D",
    onClick,
  }),

  share: (onClick: () => void): ContextualAction => ({
    id: "share",
    label: "Share",
    icon: Share2,
    onClick,
  }),

  copy: (onClick: () => void): ContextualAction => ({
    id: "copy",
    label: "Copy Link",
    icon: Copy,
    shortcut: "⌘C",
    onClick,
  }),

  compare: (onClick: () => void): ContextualAction => ({
    id: "compare",
    label: "Compare",
    icon: GitCompare,
    onClick,
  }),

  favorite: (onClick: () => void, isFavorited = false): ContextualAction => ({
    id: "favorite",
    label: isFavorited ? "Remove from Favorites" : "Add to Favorites",
    icon: Star,
    onClick,
  }),

  archive: (onClick: () => void): ContextualAction => ({
    id: "archive",
    label: "Archive",
    icon: Archive,
    onClick,
  }),

  delete: (onClick: () => void): ContextualAction => ({
    id: "delete",
    label: "Delete",
    icon: Trash2,
    destructive: true,
    onClick,
  }),

  settings: (onClick: () => void): ContextualAction => ({
    id: "settings",
    label: "Settings",
    icon: Settings,
    onClick,
  }),

  openExternal: (
    href: string,
    label = "Open in New Tab",
  ): ContextualAction => ({
    id: "open-external",
    label,
    icon: ExternalLink,
    href,
    external: true,
  }),
};

// Predefined menu configurations for different contexts
const MENU_CONFIGS = {
  jobDescription: (
    onView: () => void,
    onDownload: () => void,
    onCompare: () => void,
    onDelete?: () => void,
  ): ContextualMenuGroup[] => [
    {
      label: "Actions",
      actions: [
        COMMON_ACTIONS.view(onView),
        COMMON_ACTIONS.download(onDownload),
        COMMON_ACTIONS.compare(onCompare),
      ],
    },
    ...(onDelete
      ? [
          {
            actions: [COMMON_ACTIONS.delete(onDelete)],
          },
        ]
      : []),
  ],

  searchResult: (
    onView: () => void,
    onCompare: () => void,
    onCopy: () => void,
  ): ContextualMenuGroup[] => [
    {
      actions: [
        COMMON_ACTIONS.view(onView),
        COMMON_ACTIONS.compare(onCompare),
        COMMON_ACTIONS.copy(onCopy),
      ],
    },
  ],

  uploadedFile: (
    onView: () => void,
    onDownload: () => void,
    onDelete: () => void,
  ): ContextualMenuGroup[] => [
    {
      label: "File Actions",
      actions: [
        COMMON_ACTIONS.view(onView),
        COMMON_ACTIONS.download(onDownload),
      ],
    },
    {
      actions: [COMMON_ACTIONS.delete(onDelete)],
    },
  ],
};

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuGroup,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuRadioGroup,
  ContextualMenu,
  COMMON_ACTIONS,
  MENU_CONFIGS,
};
