import { pathToFileURL } from "node:url";

const EXERCISES = [
  ["Protected brainstorm", "BRAINSTORMING"],
  ["Silent brainwriting", "BRAINWRITING"],
  ["Affinity clustering", "AFFINITY_CLUSTERING"],
  ["Process reconstruction", "PROCESS_RECONSTRUCTION"],
  ["Assumption mapping", "ASSUMPTION_MAPPING"],
  ["POV + How Might We", "POV_HMW"],
  ["Prototype the uncertainty", "PROTOTYPE_DESIGN"],
  ["Test to learn", "TEST_DESIGN"],
] as const;

const STARTING_POINTS = [
  ["Early hunch", "EARLY_HUNCH"],
  ["Grounded exploration", "GROUNDED_EXPLORATION"],
  ["Framed challenge", "FRAMED_CHALLENGE"],
  ["Established concept", "CONCEPT"],
  ["Prototype", "PROTOTYPE"],
  ["Live product or service", "LIVE"],
  ["Unsure", "UNSURE"],
] as const;

export const DESIGN_THINK_COMMAND = {
  name: "design-think",
  description: "Facilitate a source-linked MightShape team exercise.",
  integration_types: [0],
  contexts: [0],
  options: [
    {
      type: 1,
      name: "start",
      description: "Start a collaborative exercise and open its setup form.",
      options: [
        {
          type: 3,
          name: "exercise",
          description: "Exercise to facilitate (defaults to protected brainstorm).",
          required: false,
          choices: EXERCISES.map(([name, value]) => ({ name, value })),
        },
        {
          type: 3,
          name: "visibility",
          description: "Choose whether contributions stay sealed until freeze.",
          required: false,
          choices: [
            { name: "Method default", value: "AUTO" },
            { name: "Sealed independent input", value: "SEALED" },
            { name: "Open team input", value: "OPEN" },
          ],
        },
        {
          type: 3,
          name: "starting-point",
          description: "Where the team's idea or challenge is today.",
          required: false,
          choices: STARTING_POINTS.map(([name, value]) => ({ name, value })),
        },
      ],
    },
    {
      type: 1,
      name: "status",
      description: "Show the current phase and participation count privately.",
      options: [
        {
          type: 3,
          name: "session",
          description: "MightShape session ID shown in the workshop card.",
          required: true,
          min_length: 39,
          max_length: 39,
        },
      ],
    },
    {
      type: 1,
      name: "delete",
      description: "Delete a workshop record (initiator or delegated facilitator only).",
      options: [
        {
          type: 3,
          name: "session",
          description: "MightShape session ID shown in the workshop card.",
          required: true,
          min_length: 39,
          max_length: 39,
        },
      ],
    },
    {
      type: 1,
      name: "retry",
      description: "Retry failed synthesis or delivery without changing the frozen source set.",
      options: [
        {
          type: 3,
          name: "session",
          description: "MightShape session ID shown in the workshop card.",
          required: true,
          min_length: 39,
          max_length: 39,
        },
      ],
    },
  ],
} as const;

function requiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(`${name} is required.`);
  return value;
}

export async function registerDiscordCommand(fetchImpl: typeof fetch = fetch): Promise<{
  id: string;
  name: string;
  scope: "guild" | "global";
}> {
  const applicationId = requiredEnv("DISCORD_APPLICATION_ID");
  const botToken = requiredEnv("DISCORD_BOT_TOKEN");
  const guildId = process.env.DISCORD_TEST_GUILD_ID?.trim();
  const scope = guildId ? "guild" : "global";
  const path = guildId
    ? `/applications/${encodeURIComponent(applicationId)}/guilds/${encodeURIComponent(guildId)}/commands`
    : `/applications/${encodeURIComponent(applicationId)}/commands`;
  // Discord accepts integration_types and contexts only for global commands.
  const payload = guildId
    ? Object.fromEntries(
        Object.entries(DESIGN_THINK_COMMAND).filter(
          ([key]) => key !== "integration_types" && key !== "contexts",
        ),
      )
    : DESIGN_THINK_COMMAND;
  const response = await fetchImpl(`https://discord.com/api/v10${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bot ${botToken}`,
      "Content-Type": "application/json",
      "User-Agent": "MightShape/1.0.1 (+https://github.com/grantholt-byte/mightshape)",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Discord command registration failed (${response.status}).`);
  }
  const body = (await response.json()) as { id?: string; name?: string };
  if (!body.id || body.name !== DESIGN_THINK_COMMAND.name) {
    throw new Error("Discord returned an invalid command registration response.");
  }
  return { id: body.id, name: body.name, scope };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  void registerDiscordCommand()
    .then((registered) => {
      console.log(`Registered /${registered.name} (${registered.scope}, id ${registered.id}).`);
    })
    .catch((error: unknown) => {
      console.error(error instanceof Error ? error.message : "Discord command registration failed.");
      process.exitCode = 1;
    });
}
