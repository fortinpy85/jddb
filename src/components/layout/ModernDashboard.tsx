"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  WorkflowSteps,
  JOB_PROCESSING_WORKFLOW,
} from "@/components/ui/workflow-steps";
import { SidebarNav, JOB_MANAGEMENT_NAV } from "@/components/ui/sidebar-nav";
import {
  Search,
  Plus,
  Filter,
  Download,
  Upload,
  MoreVertical,
  Eye,
  Edit,
  Trash2,
  FileText,
  Users,
  TrendingUp,
  CheckCircle,
  Clock,
  AlertCircle,
  Star,
  Calendar,
  Building,
} from "lucide-react";

interface JobItem {
  id: number;
  code: string;
  title: string;
  status: "Active" | "Draft" | "Under Review" | "Archived";
  classification: string;
  lastModified: string;
  progress: number;
  priority: "High" | "Medium" | "Low";
}

export const ModernDashboard: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState("dashboard");
  const [selectedJobs, setSelectedJobs] = useState<number[]>([]);

  // Mock data
  const jobs: JobItem[] = [
    {
      id: 1,
      code: "500710600",
      title: "Executive Management",
      status: "Active",
      classification: "EX-01",
      lastModified: "2024-03-15",
      progress: 100,
      priority: "High",
    },
    {
      id: 2,
      code: "700001",
      title: "Digital Consultant",
      status: "Under Review",
      classification: "CS-03",
      lastModified: "2024-03-14",
      progress: 75,
      priority: "Medium",
    },
    {
      id: 3,
      code: "600234",
      title: "Business Analyst",
      status: "Draft",
      classification: "AS-02",
      lastModified: "2024-03-13",
      progress: 45,
      priority: "Low",
    },
  ];

  const stats = [
    { label: "Total Jobs", value: "1,247", icon: FileText, trend: "+12%" },
    { label: "Active", value: "856", icon: CheckCircle, trend: "+5%" },
    { label: "Under Review", value: "234", icon: Clock, trend: "+18%" },
    { label: "Drafts", value: "157", icon: Edit, trend: "-3%" },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Active":
        return "bg-green-100 text-green-800 border-green-200";
      case "Draft":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "Under Review":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "Archived":
        return "bg-gray-100 text-gray-800 border-gray-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case "High":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case "Medium":
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case "Low":
        return <Star className="w-4 h-4 text-green-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Top Navigation */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">JDDB</span>
                </div>
                <span className="text-lg font-semibold">
                  Job Description Database
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <Button variant="outline" size="sm">
                Back To Main Page
              </Button>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">SPPA RT036201</span>
                <Button variant="ghost" size="sm">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 min-h-screen">
          <div className="p-6">
            {/* Current Job Info */}
            <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Star className="w-4 h-4 text-yellow-500" />
                <span className="text-sm font-medium">Job Code</span>
              </div>
              <div className="text-lg font-semibold">
                Executive Management (500710600)
              </div>
              <div className="flex items-center space-x-2 mt-2">
                <Badge className="bg-gray-200 text-gray-800">Status</Badge>
                <Badge className="bg-green-100 text-green-800">Active</Badge>
              </div>
            </div>

            {/* Navigation */}
            <SidebarNav items={JOB_MANAGEMENT_NAV} />

            {/* Workflow Actions */}
            <div className="mt-6 space-y-2">
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                Workflows
              </h4>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start"
              >
                Approve
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start"
              >
                Reject
              </Button>
            </div>

            {/* Actions */}
            <div className="mt-6 space-y-2">
              <h4 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                Actions
              </h4>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start"
              >
                <FileText className="w-4 h-4 mr-2" />
                Print PDF
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start"
              >
                <Download className="w-4 h-4 mr-2" />
                Print Word
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="w-full justify-start"
              >
                <Upload className="w-4 h-4 mr-2" />
                Email Job
              </Button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          {/* Workflow Steps */}
          <div className="mb-8">
            <WorkflowSteps steps={JOB_PROCESSING_WORKFLOW} />
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {stats.map((stat, index) => (
              <Card key={index}>
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">
                        {stat.label}
                      </p>
                      <p className="text-2xl font-bold">{stat.value}</p>
                      <p className="text-xs text-green-600 flex items-center mt-1">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        {stat.trend}
                      </p>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <stat.icon className="w-6 h-6 text-blue-600" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Main Content Area */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Job Descriptions</CardTitle>
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <Input
                      placeholder="Search jobs..."
                      className="pl-10 w-64"
                    />
                  </div>
                  <Button variant="outline" size="sm">
                    <Filter className="w-4 h-4 mr-2" />
                    Filter
                  </Button>
                  <Button size="sm">
                    <Plus className="w-4 h-4 mr-2" />
                    New Job
                  </Button>
                </div>
              </div>
            </CardHeader>

            <CardContent>
              <div className="space-y-4">
                {jobs.map((job) => (
                  <div
                    key={job.id}
                    className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                  >
                    <div className="flex items-center space-x-4">
                      <input
                        type="checkbox"
                        className="rounded border-gray-300"
                        checked={selectedJobs.includes(job.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedJobs([...selectedJobs, job.id]);
                          } else {
                            setSelectedJobs(
                              selectedJobs.filter((id) => id !== job.id),
                            );
                          }
                        }}
                      />
                      <div>
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{job.title}</span>
                          <Badge variant="outline" className="text-xs">
                            {job.code}
                          </Badge>
                          {getPriorityIcon(job.priority)}
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                          <span className="flex items-center space-x-1">
                            <Building className="w-4 h-4" />
                            <span>{job.classification}</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <Calendar className="w-4 h-4" />
                            <span>{job.lastModified}</span>
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <Badge className={getStatusColor(job.status)}>
                        {job.status}
                      </Badge>

                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>

                      <div className="flex items-center space-x-1">
                        <Button variant="ghost" size="sm">
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
