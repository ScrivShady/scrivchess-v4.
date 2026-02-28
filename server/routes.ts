import type { Express, Request, Response } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { api } from "@shared/routes";
import { z } from "zod";
import { GoogleGenAI } from "@google/genai";

// This is using Replit's AI Integrations service, which provides Gemini-compatible API access without requiring your own Gemini API key.
const ai = new GoogleGenAI({
  apiKey: process.env.AI_INTEGRATIONS_GEMINI_API_KEY,
  httpOptions: {
    apiVersion: "",
    baseUrl: process.env.AI_INTEGRATIONS_GEMINI_BASE_URL,
  },
});

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {
  
  app.get(api.analyses.list.path, async (req: Request, res: Response) => {
    const data = await storage.getAnalyses();
    res.json(data);
  });

  app.get(api.analyses.get.path, async (req: Request, res: Response) => {
    const id = Number(req.params.id);
    const data = await storage.getAnalysis(id);
    if (!data) {
      return res.status(404).json({ message: "Not found" });
    }
    res.json(data);
  });

  app.post(api.analyses.create.path, async (req: Request, res: Response) => {
    try {
      const input = api.analyses.create.input.parse(req.body);
      
      // Fetch past analyses for historical context
      const pastAnalyses = await storage.getAnalyses();
      const historicalContext = pastAnalyses.map(a => ({
        id: a.id,
        theme: a.preferences, // We don't have a structured "theme" field yet, but we can pass previous results
        result: a.resultText.substring(0, 500) // Truncate to avoid token limits
      }));

      const instruction = `
        You are the ScrivShady Coach. 
        Historical Context (Past Games): ${JSON.stringify(historicalContext)}
        
        Analyze the new game provided for the player '${input.playerName}'. 
        Preferences: Accuracy=${input.preferences.showAccuracy}, Habits=${input.preferences.showHabits}, Voice=${input.preferences.voice}, Style=${input.preferences.analysisDepth}.
        
        ${input.preferences.analysisDepth === "In-Depth" ? 
          `Provide an exhaustive, move-by-move technical breakdown. Focus on high-level strategy, alternative lines, and deep engine evaluations. 
           Include specific evaluation scores (e.g., +1.2, -0.5) for critical moments.` :
          `Provide a high-impact, visual-style summary. 
           Format specifically with these sections:
           - Stage Accuracy Table: Create a markdown table with columns: Stage (Opening, Middle, Endgame, WHOLE GAME), Accuracy (%), and Performance Summary (short qualitative labels like Elite, Lethal, Perfect, Master Level).
           - Positive (+) Attacks & Habits: Bullet points with specific move notations and descriptions of why they were good.
           - Negative (-) Weaknesses & Oversights: Bullet points covering blunders, missed checks, or positional errors with "The Oversight" and "The Consequence" details.
           - Active Challenges: 3 specific goals for next games (e.g., "Castle by move 10", "Keep your queen until the end", "No more than two pawns in opening").`
        }

        Always conclude with:
        1. New Game ID (G${pastAnalyses.length + 1})
        2. Theme Name
        3. Habit Match (Did they repeat or fix a past mistake based on the Historical Context?)
        4. Top 3 Tips for the future.
      `;

      let resultText = "";

      if (input.image) {
        // Strip the data:image/jpeg;base64, prefix
        const base64Data = input.image.replace(/^data:image\/\w+;base64,/, "");
        const mimeTypeMatch = input.image.match(/^data:(image\/\w+);base64,/);
        const mimeType = mimeTypeMatch ? mimeTypeMatch[1] : "image/jpeg";

        const response = await ai.models.generateContent({
          model: 'gemini-2.5-flash',
          contents: [
            instruction,
            {
              inlineData: {
                data: base64Data,
                mimeType,
              },
            }
          ]
        });
        resultText = response.text || "Failed to generate analysis.";
      } else if (input.pgnText) {
        const response = await ai.models.generateContent({
          model: 'gemini-2.5-flash',
          contents: instruction + "\n\n" + input.pgnText
        });
        resultText = response.text || "Failed to generate analysis.";
      } else {
        return res.status(400).json({ message: "Either image or pgnText is required" });
      }

      // Save to database
      const analysis = await storage.createAnalysis({
        playerName: input.playerName,
        preferences: input.preferences,
        pgnText: input.pgnText || null,
        imageUrl: input.image ? "uploaded_image_placeholder" : null, // we don't save the full base64 in DB to save space
        resultText: resultText
      });

      res.status(201).json(analysis);

    } catch (err) {
      if (err instanceof z.ZodError) {
        return res.status(400).json({
          message: err.errors[0].message,
          field: err.errors[0].path.join('.'),
        });
      }
      console.error("Error generating analysis:", err);
      res.status(500).json({ message: "Internal server error" });
    }
  });

  return httpServer;
}
