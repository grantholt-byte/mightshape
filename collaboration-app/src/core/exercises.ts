import type { Exercise, Visibility, WorkshopContribution } from "./contracts.js";

export interface ExerciseDefinition {
  exercise: Exercise;
  label: string;
  purpose: string;
  mindset: string;
  prompt: string;
  default_visibility: Visibility;
  contribution_kind: WorkshopContribution["kind"];
}

export const EXERCISE_DEFINITIONS: Record<Exercise, ExerciseDefinition> = {
  BRAINSTORMING: {
    exercise: "BRAINSTORMING",
    label: "Protected brainstorm",
    purpose: "Create mechanism-level breadth before the group begins judging ideas.",
    mindset: "Diverge independently. Short, incomplete, and unusual ideas are welcome; feasibility comes later.",
    prompt: "Add one idea or mechanism that approaches the challenge from a meaningfully different angle.",
    default_visibility: "SEALED",
    contribution_kind: "IDEA",
  },
  BRAINWRITING: {
    exercise: "BRAINWRITING",
    label: "Silent brainwriting",
    purpose: "Protect independent thought before social influence enters the room.",
    mindset: "Write independently. Submissions stay sealed until the facilitator freezes the set.",
    prompt: "Write one concise possibility without explaining or defending it yet.",
    default_visibility: "SEALED",
    contribution_kind: "IDEA",
  },
  AFFINITY_CLUSTERING: {
    exercise: "AFFINITY_CLUSTERING",
    label: "Affinity clustering",
    purpose: "Make relationships among source-linked notes inspectable without forcing agreement.",
    mindset: "Group provisionally. Boundary cards, contradictions, and outliers are useful.",
    prompt: "Add one atomic note, relationship, boundary card, or proposed cluster move.",
    default_visibility: "OPEN",
    contribution_kind: "NOTE",
  },
  PROCESS_RECONSTRUCTION: {
    exercise: "PROCESS_RECONSTRUCTION",
    label: "Process reconstruction",
    purpose: "Reconstruct the actual sequence, handoffs, breakdowns, and unknown transitions.",
    mindset: "Describe what really happens. Mark missing steps as unknown instead of making the path neat.",
    prompt: "Add one actual step, actor handoff, decision, breakdown, workaround, or unknown transition.",
    default_visibility: "OPEN",
    contribution_kind: "PROCESS_STEP",
  },
  ASSUMPTION_MAPPING: {
    exercise: "ASSUMPTION_MAPPING",
    label: "Assumption mapping",
    purpose: "Surface beliefs that could change the decision before the team treats them as facts.",
    mindset: "Confidence is not evidence. Name the belief and what would make it fail.",
    prompt: "Add one assumption the current direction depends on.",
    default_visibility: "SEALED",
    contribution_kind: "ASSUMPTION",
  },
  POV_HMW: {
    exercise: "POV_HMW",
    label: "POV and How Might We",
    purpose: "Create competing solution-independent frames before converging on an intervention.",
    mindset: "Use USER + NEED + INSIGHT; keep the need free of the proposed solution.",
    prompt: "Add one user, need, insight, or alternative frame that deserves consideration.",
    default_visibility: "OPEN",
    contribution_kind: "POV_COMPONENT",
  },
  PROTOTYPE_DESIGN: {
    exercise: "PROTOTYPE_DESIGN",
    label: "Prototype the uncertainty",
    purpose: "Choose the lowest-fidelity artifact that can resolve the pivotal uncertainty.",
    mindset: "Prototype to learn, not to demonstrate production polish.",
    prompt: "Add one critical assumption, learning question, minimum-fidelity move, or explicit do-not-build item.",
    default_visibility: "OPEN",
    contribution_kind: "PROTOTYPE_DECISION",
  },
  TEST_DESIGN: {
    exercise: "TEST_DESIGN",
    label: "Test to learn",
    purpose: "Define observable signals that could support, weaken, falsify, or transform the hypothesis.",
    mindset: "Look for behavior, confusion, workarounds, and surprises—not approval.",
    prompt: "Add one behavior, failure signal, surprise, comparison, or pivot rule the test should capture.",
    default_visibility: "OPEN",
    contribution_kind: "TEST_DECISION",
  },
};

export function exerciseDefinition(exercise: Exercise): ExerciseDefinition {
  return EXERCISE_DEFINITIONS[exercise];
}
