import { sql } from "drizzle-orm";
import {
  index,
  integer,
  sqliteTable,
  text,
  uniqueIndex,
} from "drizzle-orm/sqlite-core";

export const studies = sqliteTable(
  "studies",
  {
    id: text("id").primaryKey(),
    publicTokenHash: text("public_token_hash").notNull(),
    title: text("title").notNull(),
    purpose: text("purpose").notNull(),
    researchGoal: text("research_goal").notNull(),
    durationMinutes: integer("duration_minutes").notNull().default(10),
    topicsJson: text("topics_json").notNull(),
    interviewMode: text("interview_mode").notNull().default("SOLUTION_BLACKOUT"),
    conceptDescription: text("concept_description"),
    dataCollected: text("data_collected").notNull(),
    reviewerDescription: text("reviewer_description").notNull(),
    deidentifiedQuotesAllowed: integer("deidentified_quotes_allowed", {
      mode: "boolean",
    })
      .notNull()
      .default(false),
    retentionDays: integer("retention_days").notNull().default(30),
    maxTurns: integer("max_turns").notNull().default(14),
    maxParticipants: integer("max_participants").notNull().default(100),
    nextParticipantNumber: integer("next_participant_number")
      .notNull()
      .default(1),
    status: text("status").notNull().default("ACTIVE"),
    createdBy: text("created_by").notNull(),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
    updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
    expiresAt: text("expires_at").notNull(),
  },
  (table) => [
    uniqueIndex("idx_studies_public_token_hash").on(table.publicTokenHash),
    index("idx_studies_created_by").on(table.createdBy, table.createdAt),
    index("idx_studies_status_expires").on(table.status, table.expiresAt),
  ],
);

export const participants = sqliteTable(
  "participants",
  {
    id: text("id").primaryKey(),
    studyId: text("study_id")
      .notNull()
      .references(() => studies.id, { onDelete: "cascade" }),
    participantNumber: integer("participant_number").notNull(),
    sessionTokenHash: text("session_token_hash").notNull(),
    status: text("status").notNull().default("ACTIVE"),
    consentVersion: text("consent_version").notNull(),
    consentedAt: text("consented_at").notNull(),
    stateJson: text("state_json").notNull(),
    processing: integer("processing", { mode: "boolean" })
      .notNull()
      .default(false),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
    updatedAt: text("updated_at").notNull().default(sql`CURRENT_TIMESTAMP`),
    completedAt: text("completed_at"),
  },
  (table) => [
    uniqueIndex("idx_participants_session_token_hash").on(
      table.sessionTokenHash,
    ),
    uniqueIndex("idx_participants_study_number").on(
      table.studyId,
      table.participantNumber,
    ),
    index("idx_participants_study_status").on(table.studyId, table.status),
  ],
);

export const messages = sqliteTable(
  "messages",
  {
    id: text("id").primaryKey(),
    participantId: text("participant_id")
      .notNull()
      .references(() => participants.id, { onDelete: "cascade" }),
    role: text("role").notNull(),
    content: text("content").notNull(),
    provenance: text("provenance").notNull(),
    redacted: integer("redacted", { mode: "boolean" })
      .notNull()
      .default(false),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [
    index("idx_messages_participant_created").on(
      table.participantId,
      table.createdAt,
    ),
  ],
);

export const deletionReceipts = sqliteTable(
  "deletion_receipts",
  {
    id: text("id").primaryKey(),
    studyId: text("study_id").notNull(),
    participantCode: text("participant_code").notNull(),
    reason: text("reason").notNull().default("PARTICIPANT_REQUEST"),
    deletedAt: text("deleted_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [
    index("idx_deletion_receipts_study").on(table.studyId, table.deletedAt),
  ],
);

export const studyEvents = sqliteTable(
  "study_events",
  {
    id: text("id").primaryKey(),
    studyId: text("study_id")
      .notNull()
      .references(() => studies.id, { onDelete: "cascade" }),
    type: text("type").notNull(),
    detailJson: text("detail_json").notNull(),
    createdAt: text("created_at").notNull().default(sql`CURRENT_TIMESTAMP`),
  },
  (table) => [index("idx_study_events_study").on(table.studyId, table.createdAt)],
);
