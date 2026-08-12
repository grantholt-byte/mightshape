import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Design Council Research",
    template: "%s · Design Council Research",
  },
  description:
    "Transparent, privacy-conscious AI-facilitated interviews for Design Council research studies.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
