import React, { useState } from "react";
import axios from "axios";
import { Card } from "./components/Card";
import { Input } from "./components/Input";
import { Button } from "./components/Button";
import { BirdIcon as Cricket, User, Award } from 'lucide-react';

function App() {
  const [team1, setTeam1] = useState("");
  const [team2, setTeam2] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const response = await axios.post("https://team-predictor-ipl.onrender.com/analyze-teams", {
        team1,
        team2,
      });
      setResults(response.data);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-100 to-purple-100 p-8">
      <Card className="max-w-4xl mx-auto">
        <div className="p-6">
          <h1 className="text-3xl font-bold text-center mb-6">
            Cricket Performance Analyzer
          </h1>
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <Input
                type="text"
                placeholder="Enter Team 1"
                value={team1}
                onChange={(e) => setTeam1(e.target.value)}
              />
              <Input
                type="text"
                placeholder="Enter Team 2"
                value={team2}
                onChange={(e) => setTeam2(e.target.value)}
              />
            </div>
            <Button
              onClick={handleAnalyze}
              className="w-full"
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Analyze Teams"}
            </Button>
          </div>

          {results && (
            <div className="mt-8 space-y-8">
              <h2 className="text-2xl font-bold text-center">
                Analysis Results
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <ResultCard
                  title="Top Batsmen"
                  icon={<Cricket className="h-6 w-6" />}
                  players={results.batsmen}
                  scoreKey="battingScore"
                  averageKey="averageRuns"
                  averageLabel="Average Runs"
                />
                <ResultCard
                  title="Top Bowlers"
                  icon={<User className="h-6 w-6" />}
                  players={results.bowlers}
                  scoreKey="bowlingScore"
                  averageKey="averageWickets"
                  averageLabel="Average Wickets"
                />
                <ResultCard
                  title="Top All-Rounders"
                  icon={<Award className="h-6 w-6" />}
                  players={results.allrounders}
                  scoreKey="allRounderScore"
                  averageKey="averageRuns"
                  averageLabel="Average Runs"
                  showBothScores
                />
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}

function ResultCard({ title, icon, players, scoreKey, averageKey, averageLabel, showBothScores = false }) {
  return (
    <Card>
      <div className="p-4">
        <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
          {icon}
          <span>{title}</span>
        </h3>
        <div className="space-y-4">
          {players.map((player, index) => (
            <Card key={index} className="bg-gradient-to-r from-blue-50 to-purple-50">
              <div className="p-4">
                <p className="font-medium">{player.name} ({player.team})</p>
                <p>{scoreKey.charAt(0).toUpperCase() + scoreKey.slice(1)}: {player[scoreKey]}</p>
                {showBothScores && (
                  <>
                    <p>Batting Score: {player.battingScore}</p>
                    <p>Bowling Score: {player.bowlingScore}</p>
                  </>
                )}
                <p>{averageLabel}: {player[averageKey]}</p>
                {showBothScores && <p>Average Wickets: {player.averageWickets}</p>}
              </div>
            </Card>
          ))}
        </div>
      </div>
    </Card>
  );
}

export default App;

