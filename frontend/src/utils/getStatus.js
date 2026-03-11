import { STATUS_CONFIG } from "./constants";

export function getStatus(statusKey) {
  return STATUS_CONFIG[statusKey] || STATUS_CONFIG.Unknown;
}
