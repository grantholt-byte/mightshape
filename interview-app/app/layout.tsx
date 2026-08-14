import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "MightShape Research",
    template: "%s · MightShape Research",
  },
  description:
    "Transparent, privacy-conscious AI-facilitated interviews for MightShape research studies.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
