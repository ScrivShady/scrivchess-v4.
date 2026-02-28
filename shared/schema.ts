import { pgTable, text, serial, json, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const analyses = pgTable("analyses", {
  id: serial("id").primaryKey(),
  playerName: text("player_name").notNull().default("ScrivShady"),
  pgnText: text("pgn_text"),
  imageUrl: text("image_url"), // base64 string or url
  preferences: json("preferences").notNull(), // { showAccuracy: boolean, showHabits: boolean, voice: string, analysisDepth: "Standard" | "In-Depth" }
  resultText: text("result_text").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
});

export const insertAnalysisSchema = createInsertSchema(analyses).omit({ id: true, createdAt: true });

export type Analysis = typeof analyses.$inferSelect;
export type InsertAnalysis = z.infer<typeof insertAnalysisSchema>;

// Request type for generating analysis
export const analyzeRequestSchema = z.object({
  playerName: z.string().default("ScrivShady"),
  preferences: z.object({
    showAccuracy: z.boolean().default(true),
    showHabits: z.boolean().default(true),
    voice: z.enum(["Standard", "Legendary"]).default("Standard"),
    analysisDepth: z.enum(["Standard", "In-Depth"]).default("Standard"),
  }),
  pgnText: z.string().optional(),
  image: z.string().optional(), // base64 data url
});

export type AnalyzeRequest = z.infer<typeof analyzeRequestSchema>;
