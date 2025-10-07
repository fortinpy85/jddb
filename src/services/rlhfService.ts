/**
 * RLHF Service
 *
 * Frontend service for capturing and sending RLHF data to backend API.
 * Handles batching, retry logic, and localStorage synchronization.
 */

import type { RLHFEvent } from "@/hooks/useLiveImprovement";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface RLHFFeedbackCreate {
  user_id?: number;
  job_id?: number;
  event_type: "accept" | "reject" | "modify" | "generate";
  original_text: string;
  suggested_text?: string;
  final_text?: string;
  suggestion_type?: string;
  user_action: string;
  confidence?: number;
  metadata?: Record<string, any>;
}

export interface RLHFStatistics {
  total: number;
  accepted: number;
  rejected: number;
  modified: number;
  acceptance_rate: number;
  suggestion_type: string;
  days: number;
}

export interface TypeStatistics {
  suggestion_type: string;
  total: number;
  accepted: number;
  rejected: number;
  acceptance_rate: number;
  avg_confidence: number;
}

/**
 * RLHF Service Class
 */
export class RLHFService {
  private static instance: RLHFService;
  private batchQueue: RLHFFeedbackCreate[] = [];
  private batchSize = 10;
  private batchTimeout = 30000; // 30 seconds
  private batchTimer: ReturnType<typeof setTimeout> | null = null;

  private constructor() {
    // Singleton pattern
  }

  static getInstance(): RLHFService {
    if (!RLHFService.instance) {
      RLHFService.instance = new RLHFService();
    }
    return RLHFService.instance;
  }

  /**
   * Capture single feedback event
   */
  async captureFeedback(feedback: RLHFFeedbackCreate): Promise<void> {
    try {
      // Add to batch queue
      this.batchQueue.push(feedback);

      // Also save to localStorage for persistence
      this.saveToLocalStorage(feedback);

      // Send batch if size threshold reached
      if (this.batchQueue.length >= this.batchSize) {
        await this.sendBatch();
      } else {
        // Otherwise, schedule batch send
        this.scheduleBatchSend();
      }
    } catch (error) {
      console.error("Failed to capture RLHF feedback:", error);
    }
  }

  /**
   * Capture multiple feedback events from localStorage
   */
  async syncLocalStorageToBackend(): Promise<void> {
    try {
      const localData = this.getLocalStorageData();

      if (localData.length === 0) {
        return;
      }

      // Convert to feedback format
      const feedbackItems: RLHFFeedbackCreate[] = localData.map((event) => ({
        user_id: 1, // Default user for demo
        job_id: undefined,
        event_type: event.eventType,
        original_text: event.originalText,
        suggested_text: event.suggestedText,
        final_text: event.finalText,
        suggestion_type: event.suggestionType,
        user_action: event.userAction,
        confidence: event.confidence,
        metadata: event.metadata,
      }));

      // Send in batches
      const batchSize = 50;
      for (let i = 0; i < feedbackItems.length; i += batchSize) {
        const batch = feedbackItems.slice(i, i + batchSize);
        await this.sendBulkFeedback(batch);
      }

      // Clear localStorage after successful sync
      this.clearLocalStorage();
    } catch (error) {
      console.error("Failed to sync RLHF data to backend:", error);
      throw error;
    }
  }

  /**
   * Send current batch to backend
   */
  private async sendBatch(): Promise<void> {
    if (this.batchQueue.length === 0) return;

    const batch = [...this.batchQueue];
    this.batchQueue = [];

    try {
      await this.sendBulkFeedback(batch);
    } catch (error) {
      console.error("Failed to send RLHF batch:", error);
      // Re-queue failed items
      this.batchQueue.unshift(...batch);
    }

    // Clear timer
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }
  }

  /**
   * Schedule batch send
   */
  private scheduleBatchSend(): void {
    if (this.batchTimer) return;

    this.batchTimer = setTimeout(async () => {
      await this.sendBatch();
    }, this.batchTimeout);
  }

  /**
   * Send bulk feedback to API
   */
  private async sendBulkFeedback(
    feedbackItems: RLHFFeedbackCreate[],
  ): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/rlhf/feedback/bulk`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        feedback_items: feedbackItems,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to send bulk feedback: ${response.statusText}`);
    }
  }

  /**
   * Get acceptance rate statistics
   */
  async getAcceptanceRate(
    suggestionType?: string,
    days: number = 30,
  ): Promise<RLHFStatistics> {
    const params = new URLSearchParams();
    if (suggestionType) params.append("suggestion_type", suggestionType);
    params.append("days", days.toString());

    const response = await fetch(
      `${API_BASE_URL}/rlhf/statistics/acceptance-rate?${params}`,
    );

    if (!response.ok) {
      throw new Error(`Failed to get acceptance rate: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Get statistics by type
   */
  async getTypeStatistics(days: number = 30): Promise<TypeStatistics[]> {
    const response = await fetch(
      `${API_BASE_URL}/rlhf/statistics/by-type?days=${days}`,
    );

    if (!response.ok) {
      throw new Error(`Failed to get type statistics: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Export training data
   */
  async exportTrainingData(
    minConfidence: number = 0.7,
    limit: number = 1000,
  ): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/rlhf/export/training-data?min_confidence=${minConfidence}&limit=${limit}`,
    );

    if (!response.ok) {
      throw new Error(`Failed to export training data: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Save to localStorage
   */
  private saveToLocalStorage(feedback: RLHFFeedbackCreate): void {
    try {
      const existing = JSON.parse(localStorage.getItem("rlhf_pending") || "[]");
      existing.push({
        ...feedback,
        timestamp: new Date().toISOString(),
      });
      localStorage.setItem("rlhf_pending", JSON.stringify(existing));
    } catch (error) {
      console.error("Failed to save RLHF data to localStorage:", error);
    }
  }

  /**
   * Get localStorage data
   */
  private getLocalStorageData(): RLHFEvent[] {
    try {
      const data = localStorage.getItem("rlhf_live_events") || "[]";
      return JSON.parse(data);
    } catch (error) {
      console.error("Failed to read RLHF data from localStorage:", error);
      return [];
    }
  }

  /**
   * Clear localStorage
   */
  private clearLocalStorage(): void {
    try {
      localStorage.removeItem("rlhf_live_events");
      localStorage.removeItem("rlhf_pending");
    } catch (error) {
      console.error("Failed to clear RLHF data from localStorage:", error);
    }
  }

  /**
   * Force flush all pending data
   */
  async flush(): Promise<void> {
    await this.sendBatch();
    await this.syncLocalStorageToBackend();
  }
}

// Export singleton instance
export const rlhfService = RLHFService.getInstance();

// Auto-sync on page load (after delay)
if (typeof window !== "undefined") {
  setTimeout(() => {
    rlhfService.syncLocalStorageToBackend().catch(console.error);
  }, 5000); // Wait 5 seconds after page load
}

// Flush on page unload
if (typeof window !== "undefined") {
  window.addEventListener("beforeunload", () => {
    rlhfService.flush().catch(console.error);
  });
}
