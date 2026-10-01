import { apiJson } from "./api";

/**
 * The client half of notification preferences (PD-F002-B02-T04). Which categories exist, which
 * channels can be changed and what the current values are all come from the server; the client
 * only shows them and sends a person's own choice.
 */
export type NotificationChannel = {
  channel: string;
  label: string;
  enabled: boolean;
  /** The person cannot change it (the inbox copy, or an essential notice). */
  locked: boolean;
  default: boolean;
  /** The person has made their own choice (otherwise this is the default). */
  chosen: boolean;
};

export type NotificationCategory = {
  category: string;
  label: string;
  description: string;
  essential: boolean;
  channels: NotificationChannel[];
};

export type NotificationPreferences = { categories: NotificationCategory[] };

export const preferencesUrl = (workspaceId: string) =>
  `/api/v1/workspaces/${workspaceId}/notification-preferences/`;

export const setPreference = (
  workspaceId: string,
  category: string,
  channel: string,
  enabled: boolean,
) =>
  apiJson<NotificationPreferences>(preferencesUrl(workspaceId), "PUT", {
    category,
    channel,
    enabled,
  });

/** Why a channel cannot be changed, in the words shown next to it. */
export function lockedReason(
  category: NotificationCategory,
  channel: NotificationChannel,
): string {
  return category.essential
    ? "Always sent"
    : channel.channel === "inbox"
      ? "Always kept"
      : "Fixed";
}
