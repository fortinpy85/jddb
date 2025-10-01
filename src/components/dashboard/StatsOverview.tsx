import React from "react";
import { Database, CheckCircle, AlertCircle, Clock } from "lucide-react";
import { AnimatedCounter } from "@/components/ui/animated-counter";
import { StatsCard } from "@/components/ui/design-system";
import { StaggerAnimation } from "@/components/ui/transitions";
import type { ProcessingStats } from "@/lib/types";

interface StatsOverviewProps {
  stats: ProcessingStats | null;
}

export function StatsOverview({ stats }: StatsOverviewProps) {
  const statsData = [
    {
      title: "Total Jobs",
      value: (
        <AnimatedCounter
          end={stats?.total_jobs || 0}
          duration={1500}
          delay={0}
        />
      ),
      icon: Database,
      color: "blue" as const,
      tooltip: "Total number of job descriptions in the database",
    },
    {
      title: "Completed",
      value: (
        <AnimatedCounter
          end={stats?.processing_status?.completed || 0}
          duration={1500}
          delay={200}
        />
      ),
      icon: CheckCircle,
      color: "emerald" as const,
      tooltip: "Jobs that have been fully processed and are ready for use",
    },
    {
      title: "Need Review",
      value: (
        <AnimatedCounter
          end={stats?.processing_status?.needs_review || 0}
          duration={1500}
          delay={400}
        />
      ),
      icon: AlertCircle,
      color: "amber" as const,
      tooltip: "Jobs that require manual review due to processing issues",
    },
    {
      title: "Processing",
      value: (
        <AnimatedCounter
          end={
            (stats?.processing_status?.processing || 0) +
            (stats?.processing_status?.pending || 0)
          }
          duration={1500}
          delay={600}
        />
      ),
      icon: Clock,
      color: "violet" as const,
      tooltip: "Jobs currently being processed or pending processing",
    },
  ];

  return (
    <StaggerAnimation
      staggerDelay={150}
      initialDelay={100}
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
    >
      {statsData.map((stat) => (
        <StatsCard
          key={stat.title}
          title={stat.title}
          value={stat.value}
          icon={stat.icon}
          color={stat.color}
          tooltip={stat.tooltip}
        />
      ))}
    </StaggerAnimation>
  );
}
