/**
 * System Health Monitoring Page
 * Displays real-time system status, database health, and performance metrics
 */

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Activity,
  Database,
  Server,
  Cpu,
  HardDrive,
  Zap,
  AlertCircle,
  CheckCircle,
  RefreshCw,
  Clock,
} from "lucide-react";
import { apiClient } from "@/lib/api";

interface HealthStatus {
  status: "healthy" | "degraded" | "down";
  message: string;
  timestamp: string;
}

interface SystemMetrics {
  database: HealthStatus;
  api: HealthStatus;
  storage: {
    used: number;
    total: number;
    percentage: number;
  };
  response_time: {
    avg: number;
    p95: number;
    p99: number;
  };
}

export function SystemHealthPage() {
  const [loading, setLoading] = useState(false);
  const [lastCheck, setLastCheck] = useState<Date>(new Date());
  const [error, setError] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics>({
    database: {
      status: "healthy",
      message: "Checking...",
      timestamp: new Date().toISOString(),
    },
    api: {
      status: "healthy",
      message: "Checking...",
      timestamp: new Date().toISOString(),
    },
    storage: {
      used: 0,
      total: 0,
      percentage: 0,
    },
    response_time: {
      avg: 0,
      p95: 0,
      p99: 0,
    },
  });

  const checkHealth = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch detailed health data
      const healthData = await apiClient.getDetailedHealth();

      // Fetch system alerts
      const systemAlerts = await apiClient.getSystemAlerts();
      setAlerts(systemAlerts || []);

      // Extract component statuses
      const components = healthData.components || {};
      const dbComponent = components.database || {};
      const redisComponent = components.redis || {};
      const systemMetrics = healthData.metrics?.system || {};
      const appMetrics = healthData.metrics?.application || {};

      // Update database status
      const dbStatus =
        dbComponent.status === "healthy"
          ? "healthy"
          : dbComponent.status === "degraded"
            ? "degraded"
            : "down";

      setMetrics({
        database: {
          status: dbStatus,
          message:
            dbComponent.message || "PostgreSQL connection status unknown",
          timestamp: new Date().toISOString(),
        },
        api: {
          status: healthData.status === "healthy" ? "healthy" : "degraded",
          message: healthData.message || "All endpoints operational",
          timestamp: healthData.timestamp || new Date().toISOString(),
        },
        storage: {
          used:
            Math.round(((systemMetrics.disk_usage_mb || 0) / 1024) * 100) / 100,
          total:
            Math.round(((systemMetrics.disk_total_mb || 5000) / 1024) * 100) /
            100,
          percentage: systemMetrics.disk_usage_percent || 0,
        },
        response_time: {
          avg: Math.round(appMetrics.avg_response_time_ms || 0),
          p95: Math.round(appMetrics.p95_response_time_ms || 0),
          p99: Math.round(appMetrics.p99_response_time_ms || 0),
        },
      });

      setLastCheck(new Date());
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Health check failed";
      setError(errorMessage);

      setMetrics((prev) => ({
        ...prev,
        api: {
          status: "down",
          message: "API connection failed",
          timestamp: new Date().toISOString(),
        },
        database: {
          status: "down",
          message: "Unable to check database status",
          timestamp: new Date().toISOString(),
        },
      }));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();

    // Auto-refresh every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "text-green-600 bg-green-100";
      case "degraded":
        return "text-yellow-600 bg-yellow-100";
      case "down":
        return "text-red-600 bg-red-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "degraded":
        return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case "down":
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            <Activity className="w-8 h-8" />
            System Health
          </h2>
          <p className="text-gray-600 mt-1">
            Monitor system status and performance metrics
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm text-gray-500 flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Last checked: {lastCheck.toLocaleTimeString()}
          </div>
          <Button
            onClick={checkHealth}
            disabled={loading}
            size="sm"
            variant="outline"
          >
            <RefreshCw
              className={`w-4 h-4 mr-2 ${loading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3 text-red-800">
              <AlertCircle className="w-5 h-5" />
              <div>
                <div className="font-semibold">Health Check Failed</div>
                <div className="text-sm">{error}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Alerts */}
      {alerts.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <AlertCircle className="w-5 h-5" />
              System Alerts ({alerts.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {alerts.map((alert, index) => (
                <div key={index} className="flex items-start gap-2 text-sm">
                  <AlertCircle className="w-4 h-4 text-yellow-600 mt-0.5" />
                  <div>
                    <div className="font-medium">{alert.title || "Alert"}</div>
                    <div className="text-yellow-700">
                      {alert.message || alert.description}
                    </div>
                    {alert.severity && (
                      <Badge className="mt-1">{alert.severity}</Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overall Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            Overall System Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            {getStatusIcon(
              metrics.database.status === "down" ||
                metrics.api.status === "down"
                ? "down"
                : metrics.database.status === "degraded" ||
                    metrics.api.status === "degraded"
                  ? "degraded"
                  : "healthy",
            )}
            <div>
              <div className="font-semibold text-lg">
                {metrics.database.status === "down" ||
                metrics.api.status === "down"
                  ? "System Issues Detected"
                  : metrics.database.status === "degraded" ||
                      metrics.api.status === "degraded"
                    ? "System Degraded"
                    : "All Systems Operational"}
              </div>
              <div className="text-sm text-gray-600">
                {metrics.database.status === "down" ||
                metrics.api.status === "down"
                  ? "Critical services are experiencing issues"
                  : metrics.database.status === "degraded" ||
                      metrics.api.status === "degraded"
                    ? "Some services are running with reduced performance"
                    : "No issues detected across all services"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Service Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Database Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                Database
              </span>
              <Badge className={getStatusColor(metrics.database.status)}>
                {metrics.database.status}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              {getStatusIcon(metrics.database.status)}
              <div className="flex-1">
                <div className="text-sm font-medium">
                  {metrics.database.message}
                </div>
                <div className="text-xs text-gray-500">
                  PostgreSQL + pgvector
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Connection Pool</span>
                <span className="font-medium">Active</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Query Time (avg)</span>
                <span className="font-medium">
                  {metrics.response_time.avg}ms
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Status */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                API Server
              </span>
              <Badge className={getStatusColor(metrics.api.status)}>
                {metrics.api.status}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              {getStatusIcon(metrics.api.status)}
              <div className="flex-1">
                <div className="text-sm font-medium">{metrics.api.message}</div>
                <div className="text-xs text-gray-500">FastAPI + Uvicorn</div>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Response Time (p95)</span>
                <span className="font-medium">
                  {metrics.response_time.p95}ms
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Response Time (p99)</span>
                <span className="font-medium">
                  {metrics.response_time.p99}ms
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Storage and Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardDrive className="w-5 h-5" />
            Storage Usage
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Database Size</span>
              <span className="font-medium">
                {metrics.storage.used.toFixed(2)} GB /{" "}
                {metrics.storage.total.toFixed(2)} GB
              </span>
            </div>
            <Progress value={metrics.storage.percentage} className="h-2" />
            <div className="text-xs text-gray-500">
              {metrics.storage.percentage.toFixed(1)}% used
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="w-5 h-5" />
            Performance Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-1">
              <div className="text-sm text-gray-600">Average Response Time</div>
              <div className="text-2xl font-bold text-green-600">
                {metrics.response_time.avg}ms
              </div>
              <div className="text-xs text-gray-500">Excellent</div>
            </div>
            <div className="space-y-1">
              <div className="text-sm text-gray-600">95th Percentile</div>
              <div className="text-2xl font-bold text-blue-600">
                {metrics.response_time.p95}ms
              </div>
              <div className="text-xs text-gray-500">Good</div>
            </div>
            <div className="space-y-1">
              <div className="text-sm text-gray-600">99th Percentile</div>
              <div className="text-2xl font-bold text-yellow-600">
                {metrics.response_time.p99}ms
              </div>
              <div className="text-xs text-gray-500">Acceptable</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
