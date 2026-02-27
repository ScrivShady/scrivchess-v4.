import { useState, useEffect } from "react";
import { format } from "date-fns";
import { 
  Crown, History, Settings2, Sparkles, Swords, BrainCircuit, Loader2, ChevronRight
} from "lucide-react";
import { 
  SidebarProvider, 
  Sidebar, 
  SidebarContent, 
  SidebarHeader, 
  SidebarGroup, 
  SidebarGroupLabel, 
  SidebarMenu, 
  SidebarMenuItem, 
  SidebarMenuButton,
  SidebarInset,
  SidebarTrigger
} from "@/components/ui/sidebar";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";

import { useAnalyses, useAnalysis, useCreateAnalysis } from "@/hooks/use-analyses";
import { FileUploader } from "@/components/file-uploader";
import { MarkdownRenderer } from "@/components/markdown-renderer";

export default function Home() {
  const { toast } = useToast();
  
  // Settings State
  const [showAccuracy, setShowAccuracy] = useState(true);
  const [showHabits, setShowHabits] = useState(true);
  const [voice, setVoice] = useState<"Standard" | "Legendary">("Standard");
  const [playerName, setPlayerName] = useState("ScrivShady");

  // Input State
  const [activeTab, setActiveTab] = useState("image");
  const [image, setImage] = useState<string | undefined>();
  const [pgnText, setPgnText] = useState("");
  
  // Viewing State
  const [viewingId, setViewingId] = useState<number | null>(null);

  const { data: analysesHistory = [], isLoading: isLoadingHistory } = useAnalyses();
  const { data: viewingAnalysis, isLoading: isLoadingView } = useAnalysis(viewingId);
  const createAnalysis = useCreateAnalysis();

  const handleAnalyze = () => {
    if (activeTab === "image" && !image) {
      toast({ title: "No image", description: "Please upload a screenshot to analyze.", variant: "destructive" });
      return;
    }
    if (activeTab === "pgn" && !pgnText.trim()) {
      toast({ title: "No PGN", description: "Please paste PGN text to analyze.", variant: "destructive" });
      return;
    }

    setViewingId(null); // Clear past view to show loading state for new

    createAnalysis.mutate({
      playerName,
      preferences: {
        showAccuracy,
        showHabits,
        voice
      },
      image: activeTab === "image" ? image : undefined,
      pgnText: activeTab === "pgn" ? pgnText : undefined,
    }, {
      onSuccess: (data) => {
        setViewingId(data.id);
        toast({ title: "Analysis Complete", description: "The coach has reviewed your game." });
        // Optional: clear inputs
        // setImage(undefined);
        // setPgnText("");
      },
      onError: (error) => {
        toast({ title: "Analysis Failed", description: error.message, variant: "destructive" });
      }
    });
  };

  const isPending = createAnalysis.isPending;

  return (
    <SidebarProvider>
      <Sidebar className="border-r border-border/50 bg-sidebar">
        <SidebarHeader className="h-16 flex items-center px-4 border-b border-border/50">
          <div className="flex items-center gap-2 text-primary font-display font-bold text-xl">
            <Crown className="w-6 h-6 text-primary" />
            <span>ScrivShady Coach</span>
          </div>
        </SidebarHeader>
        
        <SidebarContent>
          <ScrollArea className="h-[calc(100vh-4rem)]">
            <SidebarGroup>
              <SidebarGroupLabel className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-muted-foreground mt-4 mb-2">
                <Settings2 className="w-4 h-4" /> Coach Settings
              </SidebarGroupLabel>
              <div className="px-4 py-2 space-y-6">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="accuracy" className="text-sm font-medium">Show Stage Accuracy</Label>
                    <Switch id="accuracy" checked={showAccuracy} onCheckedChange={setShowAccuracy} />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="habits" className="text-sm font-medium">Match Historical Habits</Label>
                    <Switch id="habits" checked={showHabits} onCheckedChange={setShowHabits} />
                  </div>
                </div>

                <div className="space-y-3">
                  <Label className="text-sm font-medium">Coach Voice</Label>
                  <Select value={voice} onValueChange={(val: any) => setVoice(val)}>
                    <SelectTrigger className="w-full bg-background border-border">
                      <SelectValue placeholder="Select voice" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Standard">
                        <div className="flex items-center gap-2">
                          <BrainCircuit className="w-4 h-4 text-blue-400" /> Standard
                        </div>
                      </SelectItem>
                      <SelectItem value="Legendary">
                        <div className="flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-amber-400" /> Legendary
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </SidebarGroup>

            <Separator className="my-2 bg-border/50" />

            <SidebarGroup>
              <SidebarGroupLabel className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                <History className="w-4 h-4" /> Past Analyses
              </SidebarGroupLabel>
              <SidebarMenu>
                {isLoadingHistory ? (
                  <div className="px-4 py-2 text-sm text-muted-foreground">Loading history...</div>
                ) : analysesHistory.length === 0 ? (
                  <div className="px-4 py-2 text-sm text-muted-foreground italic">No games analyzed yet.</div>
                ) : (
                  analysesHistory.map((item) => (
                    <SidebarMenuItem key={item.id}>
                      <SidebarMenuButton 
                        isActive={viewingId === item.id}
                        onClick={() => setViewingId(item.id)}
                        className="flex justify-between items-center transition-all"
                      >
                        <div className="flex flex-col items-start gap-1">
                          <span className="font-medium text-sm text-foreground/90 truncate max-w-[160px]">
                            {item.playerName} Game
                          </span>
                          <span className="text-xs text-muted-foreground">
                            {format(new Date(item.createdAt || Date.now()), "MMM d, yyyy • h:mm a")}
                          </span>
                        </div>
                        <ChevronRight className="w-4 h-4 opacity-50" />
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))
                )}
              </SidebarMenu>
            </SidebarGroup>
          </ScrollArea>
        </SidebarContent>
      </Sidebar>

      <SidebarInset className="bg-background flex flex-col h-screen overflow-hidden">
        <header className="h-16 flex items-center justify-between px-6 border-b border-border/50 shrink-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10">
          <div className="flex items-center gap-4">
            <SidebarTrigger className="-ml-2" />
            <h1 className="text-2xl font-display font-bold text-foreground flex items-center gap-3">
              <Swords className="w-6 h-6 text-primary" />
              <span>Blitz Analysis Engine</span>
            </h1>
          </div>
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary border border-primary/20 text-sm font-medium shadow-inner">
            <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            Depth 26 Engine Ready
          </div>
        </header>

        <ScrollArea className="flex-1 px-4 md:px-8 py-8">
          <div className="max-w-4xl mx-auto space-y-8 pb-12">
            
            {/* Input Section */}
            <Card className="glass-panel overflow-hidden border-border/40 shadow-2xl">
              <div className="bg-muted/30 px-6 py-4 border-b border-border/50">
                <h2 className="text-lg font-display font-semibold text-foreground/90">Submit Game for Review</h2>
              </div>
              <CardContent className="p-6">
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                  <TabsList className="grid w-full grid-cols-2 mb-6 bg-muted/50 p-1 rounded-xl">
                    <TabsTrigger value="image" className="rounded-lg py-2.5 data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-md transition-all">
                      Screenshot Upload
                    </TabsTrigger>
                    <TabsTrigger value="pgn" className="rounded-lg py-2.5 data-[state=active]:bg-background data-[state=active]:text-primary data-[state=active]:shadow-md transition-all">
                      Paste PGN
                    </TabsTrigger>
                  </TabsList>
                  
                  <div className="min-h-[300px]">
                    <TabsContent value="image" className="mt-0 outline-none">
                      <FileUploader value={image} onChange={setImage} />
                    </TabsContent>
                    
                    <TabsContent value="pgn" className="mt-0 outline-none h-full">
                      <Textarea 
                        placeholder="[Event &quot;FIDE World Cup 2023&quot;]&#10;[Site &quot;Baku AZE&quot;]&#10;[Date &quot;2023.08.09&quot;]&#10;..." 
                        className="min-h-[300px] font-mono text-sm resize-y bg-muted/20 border-border focus-visible:ring-primary/50 rounded-xl p-4"
                        value={pgnText}
                        onChange={(e) => setPgnText(e.target.value)}
                      />
                    </TabsContent>
                  </div>
                </Tabs>

                <div className="mt-8 flex justify-end">
                  <Button 
                    onClick={handleAnalyze} 
                    disabled={isPending}
                    size="lg"
                    className="w-full md:w-auto px-8 py-6 text-lg font-semibold rounded-xl bg-gradient-to-r from-primary to-amber-500 hover:from-primary/90 hover:to-amber-500/90 text-primary-foreground shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:-translate-y-0.5 transition-all duration-300"
                  >
                    {isPending ? (
                      <>
                        <Loader2 className="mr-3 h-5 w-5 animate-spin" />
                        Analyzing at Depth 26...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-3 h-5 w-5" />
                        GET COACH ADVICE
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Results Section */}
            {(isPending || viewingAnalysis || isLoadingView) && (
              <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-700">
                <div className="flex items-center gap-4">
                  <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" />
                  <span className="text-sm font-display font-bold text-muted-foreground uppercase tracking-widest px-4 py-1 border border-border rounded-full bg-background">
                    Coach Report
                  </span>
                  <div className="h-px flex-1 bg-gradient-to-r from-transparent via-border to-transparent" />
                </div>

                <Card className="glass-panel border-primary/20 shadow-2xl shadow-primary/5 relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary via-amber-300 to-primary" />
                  <CardContent className="p-8 md:p-10">
                    {isPending || isLoadingView ? (
                      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground space-y-6">
                        <div className="relative">
                          <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full" />
                          <Loader2 className="w-12 h-12 animate-spin text-primary relative z-10" />
                        </div>
                        <p className="font-display text-lg animate-pulse">
                          {isPending ? "Grandmaster is reviewing the lines..." : "Loading report..."}
                        </p>
                      </div>
                    ) : viewingAnalysis ? (
                      <MarkdownRenderer content={viewingAnalysis.resultText} />
                    ) : null}
                  </CardContent>
                </Card>
              </div>
            )}

          </div>
        </ScrollArea>
      </SidebarInset>
    </SidebarProvider>
  );
}
