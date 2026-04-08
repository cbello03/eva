import { describe, it, expect, beforeEach, vi } from "vitest";

// Mock apiClient before importing the module under test
vi.mock("@/lib/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const { apiClient } = await import("@/lib/api-client");
const {
  getNotifications,
  getUnreadCount,
  markRead,
  markAllRead,
} = await import("@/features/notifications/api");

const mockGet = apiClient.get as ReturnType<typeof vi.fn>;
const mockPost = apiClient.post as ReturnType<typeof vi.fn>;

describe("notifications/api", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getNotifications", () => {
    it("fetches paginated notifications with default params", async () => {
      const payload = {
        count: 2,
        next_offset: null,
        results: [
          { id: 1, title: "Test", body: "Body", notification_type: "achievement", data: {}, channel: "in_app", is_read: false, created_at: "2025-01-01T00:00:00Z" },
          { id: 2, title: "Test 2", body: "Body 2", notification_type: "forum_reply", data: {}, channel: "in_app", is_read: true, created_at: "2025-01-01T00:00:00Z" },
        ],
      };
      mockGet.mockResolvedValueOnce({ data: payload });

      const result = await getNotifications();

      expect(mockGet).toHaveBeenCalledWith("/notifications", {
        params: { offset: 0, limit: 20 },
      });
      expect(result).toEqual(payload);
      expect(result.results).toHaveLength(2);
    });

    it("passes custom offset and limit", async () => {
      mockGet.mockResolvedValueOnce({ data: { count: 0, next_offset: null, results: [] } });

      await getNotifications(40, 10);

      expect(mockGet).toHaveBeenCalledWith("/notifications", {
        params: { offset: 40, limit: 10 },
      });
    });
  });

  describe("getUnreadCount", () => {
    it("returns the unread count", async () => {
      mockGet.mockResolvedValueOnce({ data: { count: 5 } });

      const result = await getUnreadCount();

      expect(mockGet).toHaveBeenCalledWith("/notifications/unread-count");
      expect(result).toEqual({ count: 5 });
    });
  });

  describe("markRead", () => {
    it("marks a single notification as read", async () => {
      const notification = {
        id: 42,
        title: "Read me",
        body: "Body",
        notification_type: "achievement",
        data: {},
        channel: "in_app",
        is_read: true,
        created_at: "2025-01-01T00:00:00Z",
      };
      mockPost.mockResolvedValueOnce({ data: notification });

      const result = await markRead(42);

      expect(mockPost).toHaveBeenCalledWith("/notifications/42/read");
      expect(result.is_read).toBe(true);
    });
  });

  describe("markAllRead", () => {
    it("marks all notifications as read", async () => {
      mockPost.mockResolvedValueOnce({ data: { updated: 7 } });

      const result = await markAllRead();

      expect(mockPost).toHaveBeenCalledWith("/notifications/read-all");
      expect(result.updated).toBe(7);
    });
  });
});
