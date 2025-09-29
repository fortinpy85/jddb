/**
 * JDDB UI Showcase Component
 * Demonstrates the improved user interface components and patterns
 */

"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ContentSection } from "@/components/layout/JDDBLayout";
import { LoadingState, ErrorState, StatusIndicator } from "@/components/ui/states";
import EmptyState from "@/components/ui/empty-state";
import { FadeTransition, StaggerAnimation, HoverTransition } from "@/components/ui/transitions";
import { EnhancedCard, FeatureCard, MetricCard } from "@/components/ui/enhanced-card";
import { EnhancedNavigation, EnhancedBreadcrumb } from "@/components/ui/enhanced-navigation";
import { EnhancedSearch, EnhancedFileUpload, EnhancedInput } from "@/components/ui/enhanced-forms";
import { ActionButton, StatsCard } from "@/components/ui/design-system";
import { cn } from "@/lib/utils";
import {
  Database,
  CheckCircle,
  AlertCircle,
  Clock,
  BarChart3,
  FileText,
  Upload,
  Search,
  Edit3,
  GitCompare,
  Activity,
  Palette,
  Star,
  TrendingUp,
  Users,
  Zap,
  Shield,
  Smartphone,
  Monitor,
  Globe
} from "lucide-react";

export function UIShowcase() {
  const [activeDemo, setActiveDemo] = useState("overview");
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [showError, setShowError] = useState(false);

  const demoSections = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "layout", label: "Layout System", icon: Monitor },
    { id: "components", label: "Components", icon: Palette },
    { id: "states", label: "States", icon: Activity },
    { id: "transitions", label: "Transitions", icon: Zap },
    { id: "responsive", label: "Responsive", icon: Smartphone },
  ];

  const renderOverview = () => (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center space-x-3">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg blur opacity-20"></div>
            <Database className="relative w-12 h-12 text-blue-600" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 bg-clip-text text-transparent">
            JDDB UI Improvements
          </h1>
        </div>
        <p className="text-lg text-slate-600 dark:text-slate-400 max-w-3xl mx-auto">
          Enhanced user interface with consistent layout, modern design patterns, and improved accessibility
        </p>
      </div>

      <StaggerAnimation staggerDelay={100} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[
          {
            title: "Consistent Layout System",
            description: "Unified header, navigation, and content structure across all pages",
            icon: Monitor,
            color: "blue"
          },
          {
            title: "Enhanced Components",
            description: "Modern cards, forms, navigation with improved interactions",
            icon: Palette,
            color: "emerald"
          },
          {
            title: "Visual Continuity",
            description: "JDDB branding maintained throughout the application",
            icon: Database,
            color: "violet"
          },
          {
            title: "Responsive Design",
            description: "Optimized for mobile, tablet, and desktop devices",
            icon: Smartphone,
            color: "amber"
          },
          {
            title: "Smooth Transitions",
            description: "Animated page changes and micro-interactions",
            icon: Zap,
            color: "red"
          },
          {
            title: "Best Practices",
            description: "Accessibility, performance, and usability focused",
            icon: Shield,
            color: "green"
          }
        ].map((feature, index) => (
          <FeatureCard
            key={index}
            title={feature.title}
            description={feature.description}
            icon={feature.icon}
          />
        ))}
      </StaggerAnimation>
    </div>
  );

  const renderLayoutDemo = () => (
    <div className="space-y-8">
      <ContentSection
        title="Layout System Components"
        subtitle="Consistent structure across all pages"
        icon={Monitor}
        variant="highlighted"
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-900 dark:text-slate-100">Header Components</h4>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>• Consistent JDDB logo and branding</li>
              <li>• Theme toggle integration</li>
              <li>• Real-time statistics display</li>
              <li>• Responsive design for all screen sizes</li>
            </ul>
          </div>
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-900 dark:text-slate-100">Navigation System</h4>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>• Tab-based navigation with icons</li>
              <li>• Keyboard navigation support</li>
              <li>• Active state indicators</li>
              <li>• Mobile-optimized overflow handling</li>
            </ul>
          </div>
        </div>
      </ContentSection>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <MetricCard
          title="Layout Consistency"
          value="100%"
          icon={CheckCircle}
          color="emerald"
          change={{ value: 45, period: "last month" }}
        />
        <MetricCard
          title="Mobile Responsiveness"
          value="100%"
          icon={Smartphone}
          color="blue"
          change={{ value: 60, period: "improvement" }}
        />
      </div>
    </div>
  );

  const renderComponentsDemo = () => (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <EnhancedCard
          title="Enhanced Cards"
          subtitle="Modern card designs"
          description="Multiple variants including elevated, outlined, and gradient styles with hover effects and smooth animations."
          variant="gradient"
          interactive
          badges={[{ label: "New", variant: "secondary" }]}
        />

        <EnhancedCard
          title="Action Components"
          subtitle="Interactive elements"
          description="Buttons, badges, and controls with consistent styling and behavior patterns."
          variant="elevated"
          interactive
          badges={[{ label: "Improved", variant: "outline" }]}
        />

        <EnhancedCard
          title="Form Elements"
          subtitle="Enhanced inputs"
          description="Advanced search, file upload, and input components with validation and user feedback."
          variant="outlined"
          interactive
          badges={[{ label: "Enhanced", variant: "default" }]}
        />
      </div>

      <ContentSection
        title="Interactive Demonstrations"
        icon={Palette}
        variant="highlighted"
      >
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <ActionButton variant="primary" icon={CheckCircle}>
              Primary Action
            </ActionButton>
            <ActionButton variant="outline" color="emerald" icon={Upload}>
              Upload Files
            </ActionButton>
            <ActionButton variant="outline" color="blue" icon={Search}>
              Search Jobs
            </ActionButton>
            <ActionButton variant="outline" color="amber" icon={GitCompare}>
              Compare
            </ActionButton>
          </div>

          <div className="flex flex-wrap gap-2">
            <StatusIndicator status="success" message="Connected" />
            <StatusIndicator status="loading" message="Processing" />
            <StatusIndicator status="warning" message="Review Required" />
            <StatusIndicator status="error" message="Failed" />
          </div>
        </div>
      </ContentSection>
    </div>
  );

  const renderStatesDemo = () => (
    <div className="space-y-8">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6">
          <h4 className="font-semibold mb-4">Loading States</h4>
          <LoadingState size="sm" message="Loading data..." />
        </Card>

        <Card className="p-6">
          <h4 className="font-semibold mb-4">Empty States</h4>
          <EmptyState
            icon="search"
            title="No Results"
            description="Try adjusting your search criteria"
            action={{
              label: "Clear Filters",
              onClick: () => console.log("Clear filters")
            }}
          />
        </Card>

        <Card className="p-6">
          <h4 className="font-semibold mb-4">Error States</h4>
          <ErrorState
            variant="warning"
            title="Connection Issue"
            message="Check your network connection"
            actionLabel="Retry"
            showRetry
          />
        </Card>
      </div>
    </div>
  );

  const renderTransitionsDemo = () => (
    <div className="space-y-8">
      <ContentSection
        title="Animation Demonstrations"
        icon={Zap}
        variant="highlighted"
      >
        <div className="space-y-6">
          <div className="flex gap-4">
            <Button
              onClick={() => setLoadingDemo(!loadingDemo)}
              variant="outline"
            >
              Toggle Loading Demo
            </Button>
            <Button
              onClick={() => setShowError(!showError)}
              variant="outline"
            >
              Toggle Error Demo
            </Button>
          </div>

          <FadeTransition show={loadingDemo}>
            <div className="p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <LoadingState message="Demonstrating fade transition..." />
            </div>
          </FadeTransition>

          <FadeTransition show={showError}>
            <div className="p-6 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <ErrorState
                title="Demo Error State"
                message="This is a demonstration of the error state with transitions"
                showRetry={false}
              />
            </div>
          </FadeTransition>
        </div>
      </ContentSection>

      <StaggerAnimation staggerDelay={200} className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {["First Item", "Second Item", "Third Item"].map((item, index) => (
          <Card key={index} className="p-6 text-center">
            <h5 className="font-medium">{item}</h5>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
              Staggered animation demo
            </p>
          </Card>
        ))}
      </StaggerAnimation>
    </div>
  );

  const renderResponsiveDemo = () => (
    <div className="space-y-8">
      <ContentSection
        title="Responsive Design Features"
        icon={Smartphone}
        variant="highlighted"
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-900 dark:text-slate-100">Mobile Optimizations</h4>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>• Touch-friendly tap targets (44px minimum)</li>
              <li>• Optimized navigation for small screens</li>
              <li>• Responsive typography scaling</li>
              <li>• Safe area support for modern devices</li>
              <li>• Performance-optimized animations</li>
            </ul>
          </div>
          <div className="space-y-4">
            <h4 className="font-semibold text-slate-900 dark:text-slate-100">Accessibility Features</h4>
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>• Keyboard navigation support</li>
              <li>• Screen reader compatibility</li>
              <li>• High contrast mode support</li>
              <li>• Reduced motion preferences</li>
              <li>• Focus management and indicators</li>
            </ul>
          </div>
        </div>
      </ContentSection>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg text-center">
          <Monitor className="w-8 h-8 mx-auto mb-2 text-green-600" />
          <p className="text-sm font-medium">Desktop</p>
          <p className="text-xs text-slate-600 dark:text-slate-400">Full experience</p>
        </div>
        <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-center">
          <div className="w-8 h-8 mx-auto mb-2 bg-blue-600 rounded"></div>
          <p className="text-sm font-medium">Tablet</p>
          <p className="text-xs text-slate-600 dark:text-slate-400">Optimized layout</p>
        </div>
        <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg text-center">
          <Smartphone className="w-8 h-8 mx-auto mb-2 text-purple-600" />
          <p className="text-sm font-medium">Mobile</p>
          <p className="text-xs text-slate-600 dark:text-slate-400">Touch-optimized</p>
        </div>
        <div className="p-4 bg-amber-50 dark:bg-amber-900/20 rounded-lg text-center">
          <Globe className="w-8 h-8 mx-auto mb-2 text-amber-600" />
          <p className="text-sm font-medium">Universal</p>
          <p className="text-xs text-slate-600 dark:text-slate-400">Accessible</p>
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch (activeDemo) {
      case "overview":
        return renderOverview();
      case "layout":
        return renderLayoutDemo();
      case "components":
        return renderComponentsDemo();
      case "states":
        return renderStatesDemo();
      case "transitions":
        return renderTransitionsDemo();
      case "responsive":
        return renderResponsiveDemo();
      default:
        return renderOverview();
    }
  };

  return (
    <div className="space-y-6">
      {/* Navigation */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-2">
          {demoSections.map((section) => (
            <Button
              key={section.id}
              variant={activeDemo === section.id ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveDemo(section.id)}
              className="flex items-center gap-2"
            >
              <section.icon className="w-4 h-4" />
              {section.label}
            </Button>
          ))}
        </div>
      </Card>

      {/* Content */}
      <FadeTransition show={true}>
        {renderContent()}
      </FadeTransition>

      {/* Footer */}
      <Card className="p-6 text-center">
        <div className="flex items-center justify-center space-x-2 text-blue-600 mb-2">
          <Database className="w-5 h-5" />
          <span className="font-semibold">JDDB - Job Description Database</span>
        </div>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Enhanced user interface with modern design patterns and consistent branding
        </p>
      </Card>
    </div>
  );
}