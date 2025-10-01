/**
 * Typing Indicator Component
 *
 * Displays real-time typing indicators for collaborative editing with:
 * - Animated typing dots
 * - User identification
 * - Multiple user support
 * - Fade in/out transitions
 */

"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";

export interface TypingUser {
  userId: number;
  username: string;
  color?: string;
}

interface TypingIndicatorProps {
  typingUsers: TypingUser[];
  maxVisible?: number;
  className?: string;
}

export const TypingIndicator: React.FC<TypingIndicatorProps> = ({
  typingUsers,
  maxVisible = 3,
  className = "",
}) => {
  if (typingUsers.length === 0) return null;

  const visibleUsers = typingUsers.slice(0, maxVisible);
  const hiddenCount = Math.max(0, typingUsers.length - maxVisible);

  const getUserText = () => {
    if (visibleUsers.length === 1) {
      return `${visibleUsers[0].username} is typing`;
    }

    if (visibleUsers.length === 2) {
      return `${visibleUsers[0].username} and ${visibleUsers[1].username} are typing`;
    }

    const names = visibleUsers.map((u) => u.username).join(", ");
    if (hiddenCount > 0) {
      return `${names}, and ${hiddenCount} ${hiddenCount === 1 ? "other" : "others"} are typing`;
    }

    return `${names} are typing`;
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.2 }}
        className={`flex items-center gap-2 text-xs text-gray-600 ${className}`}
      >
        <span>{getUserText()}</span>
        <TypingDots />
      </motion.div>
    </AnimatePresence>
  );
};

/**
 * Animated Typing Dots
 */
export const TypingDots: React.FC<{ className?: string }> = ({
  className = "",
}) => {
  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="w-1 h-1 bg-gray-400 rounded-full"
          animate={{
            y: [0, -4, 0],
            opacity: [0.4, 1, 0.4],
          }}
          transition={{
            duration: 0.6,
            repeat: Infinity,
            delay: i * 0.15,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
};

/**
 * Inline Typing Indicator
 * Minimal version for compact spaces
 */
export const InlineTypingIndicator: React.FC<{
  typingUsers: TypingUser[];
}> = ({ typingUsers }) => {
  if (typingUsers.length === 0) return null;

  return (
    <div className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">
      <TypingDots />
      <span>
        {typingUsers.length === 1
          ? typingUsers[0].username
          : `${typingUsers.length} users`}
      </span>
    </div>
  );
};

/**
 * Floating Typing Indicator
 * Positioned indicator for editor interfaces
 */
export const FloatingTypingIndicator: React.FC<{
  typingUsers: TypingUser[];
  position?: "top" | "bottom";
}> = ({ typingUsers, position = "bottom" }) => {
  if (typingUsers.length === 0) return null;

  const positionClasses =
    position === "top"
      ? "top-2 left-2"
      : "bottom-2 left-2";

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        className={`absolute ${positionClasses} z-10`}
      >
        <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="flex -space-x-2">
            {typingUsers.slice(0, 3).map((user) => (
              <div
                key={user.userId}
                className={`w-5 h-5 rounded-full border-2 border-white flex items-center justify-center text-xs font-medium text-white ${
                  user.color || "bg-blue-500"
                }`}
                title={user.username}
              >
                {user.username.slice(0, 1).toUpperCase()}
              </div>
            ))}
          </div>
          <TypingDots />
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

/**
 * Hook for managing typing indicator state
 */
export const useTypingIndicator = (
  userId: number,
  onTypingChange?: (isTyping: boolean) => void,
  debounceMs: number = 1000
) => {
  const [isTyping, setIsTyping] = React.useState(false);
  const timeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  const startTyping = React.useCallback(() => {
    if (!isTyping) {
      setIsTyping(true);
      onTypingChange?.(true);
    }

    // Clear existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timeout to stop typing indicator
    timeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      onTypingChange?.(false);
    }, debounceMs);
  }, [isTyping, onTypingChange, debounceMs]);

  const stopTyping = React.useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setIsTyping(false);
    onTypingChange?.(false);
  }, [onTypingChange]);

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return { isTyping, startTyping, stopTyping };
};