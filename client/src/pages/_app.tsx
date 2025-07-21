// src/pages/_app.tsx
import type { AppProps } from "next/app";
import "@/index.css"; // 전역 CSS
import { ThemeProvider } from "@/components/ui/theme-provider"; // 다크/라이트 모드 지원
import { Toaster } from "@/components/ui/toaster"; // Toast 메시지
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "@/lib/queryClient"; // React Query Client

export default function MyApp({ Component, pageProps }: AppProps) {
  return (
    <ThemeProvider defaultTheme="dark" storageKey="ui-theme">
      <QueryClientProvider client={queryClient}>
        <Component {...pageProps} />
        <Toaster />
      </QueryClientProvider>
    </ThemeProvider>
  );
}
