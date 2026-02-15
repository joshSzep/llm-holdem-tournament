/**
 * Chat Zustand store — holds chat and action log messages.
 */

import { create } from "zustand";

export interface ChatEntry {
  id: string;
  seat_index: number;
  name: string;
  message: string;
  timestamp: string;
  /** Whether this is a system/action message vs player/AI chat */
  isSystem: boolean;
}

interface ChatStore {
  /** All chat messages for the current game */
  messages: ChatEntry[];

  /** Actions */
  addMessage: (entry: ChatEntry) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],

  addMessage: (entry) =>
    set((state) => ({
      messages: [...state.messages, entry],
    })),

  clearMessages: () => set({ messages: [] }),
}));
