import React from "react";
import { Users, TrendingUp } from "lucide-react";
import { ContentSection } from "@/components/layout/JDDBLayout";
import { getClassificationLevel } from "@/lib/utils";
import type { ProcessingStats } from "@/lib/types";

interface ChartsSectionProps {
  stats: ProcessingStats;
}

export function ChartsSection({ stats }: ChartsSectionProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Classification Distribution */}
      <ContentSection
        title="Jobs by Classification"
        icon={Users}
        variant="highlighted"
      >
        <div className="space-y-4">
          {Object.entries(stats.by_classification).map(([classification, count]) => (
            <div
              key={classification}
              className="flex items-center justify-between group hover:bg-blue-50/50 p-3 -m-3 rounded-lg transition-all duration-200"
            >
              <div className="flex items-center">
                <div className="w-3 h-3 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full mr-3 group-hover:scale-110 transition-transform duration-200 shadow-sm"></div>
                <span className="text-sm font-semibold text-slate-700 group-hover:text-blue-700 transition-colors duration-200">
                  {classification}
                </span>
                <span className="text-xs text-slate-500 ml-2 font-medium">
                  ({getClassificationLevel(classification)})
                </span>
              </div>
              <span className="text-sm font-bold text-slate-800 bg-slate-100/50 px-3 py-1.5 rounded-full group-hover:bg-blue-100/50 group-hover:text-blue-700 transition-all duration-200">
                {count}
              </span>
            </div>
          ))}
        </div>
      </ContentSection>

      {/* Language Distribution */}
      <ContentSection
        title="Jobs by Language"
        icon={TrendingUp}
        variant="highlighted"
      >
        <div className="space-y-4">
          {Object.entries(stats.by_language).map(([language, count]) => (
            <div
              key={language}
              className="flex items-center justify-between group hover:bg-emerald-50/50 p-3 -m-3 rounded-lg transition-all duration-200"
            >
              <div className="flex items-center">
                <div className="w-3 h-3 bg-gradient-to-r from-emerald-500 to-green-500 rounded-full mr-3 group-hover:scale-110 transition-transform duration-200 shadow-sm"></div>
                <span className="text-sm font-semibold text-slate-700 group-hover:text-emerald-700 transition-colors duration-200">
                  {language === "en" ? "English" : language === "fr" ? "French" : language}
                </span>
              </div>
              <span className="text-sm font-bold text-slate-800 bg-slate-100/50 px-3 py-1.5 rounded-full group-hover:bg-emerald-100/50 group-hover:text-emerald-700 transition-all duration-200">
                {count}
              </span>
            </div>
          ))}
        </div>
      </ContentSection>
    </div>
  );
}