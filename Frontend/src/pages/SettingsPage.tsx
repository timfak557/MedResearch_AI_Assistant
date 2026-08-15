import { Monitor, Moon, Sun } from "lucide-react";
import { useApp } from "@/context/AppContext";
import { useStatistics } from "@/hooks/useSearch";
import type { Theme } from "@/lib/storage";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { SystemStatus } from "@/components/system/SystemStatus";

const THEMES: Array<{ value: Theme; label: string; icon: typeof Sun }> = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

export function SettingsPage() {
  const { theme, setTheme, preferences, updatePreferences } = useApp();
  const statistics = useStatistics();

  return (
    <div className="mx-auto h-full max-w-2xl space-y-4 overflow-y-auto px-4 py-6 md:px-8">
      <h1 className="text-lg font-semibold">Settings</h1>

      <Card>
        <CardHeader><CardTitle>Appearance</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          {THEMES.map(({ value, label, icon: Icon }) => (
            <Button
              key={value}
              variant={theme === value ? "default" : "outline"}
              size="sm"
              aria-pressed={theme === value}
              onClick={() => setTheme(value)}
            >
              <Icon className="h-3.5 w-3.5" aria-hidden /> {label}
            </Button>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Research Preferences</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between gap-4">
            <label htmlFor="pref-topk" className="text-sm">Default results per search</label>
            <Select
              id="pref-topk"
              className="w-24"
              value={preferences.defaultTopK}
              onChange={(event) =>
                updatePreferences({ defaultTopK: Number(event.target.value) })
              }
            >
              {[3, 5, 10].map((n) => <option key={n} value={n}>{n}</option>)}
            </Select>
          </div>
          {(
            [
              ["showEvidence", "Show evidence panel"],
              ["showScores", "Show relevance scores"],
              ["compactMode", "Compact mode"],
              ["storeHistory", "Store research history on this device"],
            ] as const
          ).map(([key, label]) => (
            <div key={key} className="flex items-center justify-between gap-4">
              <span className="text-sm">{label}</span>
              <Switch
                checked={preferences[key]}
                onCheckedChange={(checked) => updatePreferences({ [key]: checked })}
                label={label}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>System</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <SystemStatus />
          {statistics.data && (
            <p className="border-t border-border pt-3 text-[12px] text-muted-foreground">
              Knowledge base: {statistics.data.total_chunks?.toLocaleString() ?? "—"} evidence
              chunks · {statistics.data.sources ?? "—"} sources ·{" "}
              {statistics.data.question_types ?? "—"} question types
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>About</CardTitle></CardHeader>
        <CardContent className="text-[13px] leading-relaxed text-muted-foreground">
          MedResearch AI provides evidence-grounded educational medical information from the
          MedQuAD knowledge base. It is not a medical device and does not provide diagnosis or
          treatment. See the About page for details.
        </CardContent>
      </Card>
    </div>
  );
}
