import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatKoreanWon(value: number | string | null | undefined): string {
  if (value == null) return "N/A";

  const numeric = typeof value === "string" ? parseInt(value, 10) : value;

  const EOK = 100_000_000;
  const JO = 10_000 * EOK;

  if (numeric < EOK) {
    return `${numeric.toLocaleString("ko-KR")}원`;
  }

  const jo = Math.floor(numeric / JO);
  const eok = Math.floor((numeric % JO) / EOK);

  const joPart = jo > 0 ? `${jo.toLocaleString("ko-KR")}조` : "";
  const eokPart =
    eok > 0 ? `${eok.toLocaleString("ko-KR")}억원` : jo > 0 ? "" : "원";

  return `${joPart}${jo > 0 && eok > 0 ? " " : ""}${eokPart}`.trim();
}
