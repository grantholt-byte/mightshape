CREATE TABLE `deletion_receipts` (
	`id` text PRIMARY KEY NOT NULL,
	`study_id` text NOT NULL,
	`participant_code` text NOT NULL,
	`reason` text DEFAULT 'PARTICIPANT_REQUEST' NOT NULL,
	`deleted_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL
);
--> statement-breakpoint
CREATE INDEX `idx_deletion_receipts_study` ON `deletion_receipts` (`study_id`,`deleted_at`);--> statement-breakpoint
CREATE TABLE `messages` (
	`id` text PRIMARY KEY NOT NULL,
	`participant_id` text NOT NULL,
	`role` text NOT NULL,
	`content` text NOT NULL,
	`provenance` text NOT NULL,
	`redacted` integer DEFAULT false NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY (`participant_id`) REFERENCES `participants`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `idx_messages_participant_created` ON `messages` (`participant_id`,`created_at`);--> statement-breakpoint
CREATE TABLE `participants` (
	`id` text PRIMARY KEY NOT NULL,
	`study_id` text NOT NULL,
	`participant_number` integer NOT NULL,
	`session_token_hash` text NOT NULL,
	`status` text DEFAULT 'ACTIVE' NOT NULL,
	`consent_version` text NOT NULL,
	`consented_at` text NOT NULL,
	`state_json` text NOT NULL,
	`processing` integer DEFAULT false NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`completed_at` text,
	FOREIGN KEY (`study_id`) REFERENCES `studies`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_participants_session_token_hash` ON `participants` (`session_token_hash`);--> statement-breakpoint
CREATE UNIQUE INDEX `idx_participants_study_number` ON `participants` (`study_id`,`participant_number`);--> statement-breakpoint
CREATE INDEX `idx_participants_study_status` ON `participants` (`study_id`,`status`);--> statement-breakpoint
CREATE TABLE `studies` (
	`id` text PRIMARY KEY NOT NULL,
	`public_token_hash` text NOT NULL,
	`title` text NOT NULL,
	`purpose` text NOT NULL,
	`research_goal` text NOT NULL,
	`duration_minutes` integer DEFAULT 10 NOT NULL,
	`topics_json` text NOT NULL,
	`interview_mode` text DEFAULT 'SOLUTION_BLACKOUT' NOT NULL,
	`concept_description` text,
	`data_collected` text NOT NULL,
	`reviewer_description` text NOT NULL,
	`deidentified_quotes_allowed` integer DEFAULT false NOT NULL,
	`retention_days` integer DEFAULT 30 NOT NULL,
	`max_turns` integer DEFAULT 14 NOT NULL,
	`max_participants` integer DEFAULT 100 NOT NULL,
	`next_participant_number` integer DEFAULT 1 NOT NULL,
	`status` text DEFAULT 'ACTIVE' NOT NULL,
	`created_by` text NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`updated_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	`expires_at` text NOT NULL
);
--> statement-breakpoint
CREATE UNIQUE INDEX `idx_studies_public_token_hash` ON `studies` (`public_token_hash`);--> statement-breakpoint
CREATE INDEX `idx_studies_created_by` ON `studies` (`created_by`,`created_at`);--> statement-breakpoint
CREATE INDEX `idx_studies_status_expires` ON `studies` (`status`,`expires_at`);--> statement-breakpoint
CREATE TABLE `study_events` (
	`id` text PRIMARY KEY NOT NULL,
	`study_id` text NOT NULL,
	`type` text NOT NULL,
	`detail_json` text NOT NULL,
	`created_at` text DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY (`study_id`) REFERENCES `studies`(`id`) ON UPDATE no action ON DELETE cascade
);
--> statement-breakpoint
CREATE INDEX `idx_study_events_study` ON `study_events` (`study_id`,`created_at`);--> statement-breakpoint
PRAGMA optimize;
