import type { Metadata } from "next";
import { InterviewClient } from "./InterviewClient";

export const metadata: Metadata = {
  title: "Research interview",
  robots: { index: false, follow: false, nocache: true },
};

export const dynamic = "force-dynamic";

export default async function StudyPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return <InterviewClient token={token} />;
}
