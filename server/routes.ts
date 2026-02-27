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
      
      const instruction = `
        Analyze this chess game for the player '${input.playerName}'. 
        Preferences: Accuracy=${input.preferences.showAccuracy}, Habits=${input.preferences.showHabits}, Voice=${input.preferences.voice}.
        
        Focus on:
        1. Theme Name.
        2. Accuracy (Opening/Middle/End).
        3. Positive Habits.
        4. Negative Habits (check for f-pawn pushes or hanging queens).
        5. Top 3 Tips for the future.
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
