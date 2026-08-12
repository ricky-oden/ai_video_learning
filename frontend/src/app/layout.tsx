import type { Metadata } from "next";
import type { ReactNode } from "react";

import { SiteNav } from "@/components/site-nav";
import { AuthProvider } from "@/providers/auth-provider";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Video Learning",
  description: "AI-LEARNING-V1 learning foundation",
};

export default function RootLayout({
  children,
}: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ja">
      <body>
        <AuthProvider>
          <SiteNav />
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
