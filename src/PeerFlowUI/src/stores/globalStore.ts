// @ts-nocheck
import { defineStore } from "pinia";
import axios from "axios";

interface Student {
  id: string;
  name: string;
  email: string;
}

export interface Assignment {
  id: string;
  name: string;
  description: string;
  submissonDeadline: string;
  createdDate: string;
  lastModifiedDate: string;
  teacherId: string;
  involvedStudents: Student[];
}

export interface PRPairing {
  ReviewerStudentID: string;
  RevieweeSubmissionID: string;
  Status: string;
  ReviewResults: Record<string, any> | null;
}

interface Criterion {
  Title: string;
  Description: string;
  MinScore: number;
  MaxScore: number;
}

interface Rubric {
  id?: string;
  Criteria: Criterion[];
} 

export interface PeerReviewAssignment{
  id: string;
  AssignmentID: string;
  ReviewDeadline: string;
  RubricID: string;
  Rubric: Rubric;
  Status: string;
  ReviewerAssignmentMode: string;
  NumberOfReviewersPerSubmission: number;
  PeerReviewPairings: PRPairing[];
}

interface AssignmentSubmission {
  _id: string;
  AssignmentID: string;
  Status: string;
  StudentID: string;
  TextContent: string;
  Attachments: {
    FileName: string;
    FileType: string;
    FileReference: string;
  }[];
}


export const useGlobalStore = defineStore("global", {
  state: () => ({
    access_token: null as string | null,
    refresh_token: null as string | null,
    user: null as Record<string, any> | null,

    assignment: null as Assignment | null,
    peerReview: null as Record<string, any> | null,
    assignmentSubmissions: [] as AssignmentSubmission[],
  }),
    actions: {
    setUser(userData: Record<string, any>) {
      this.user = userData;
      if (process.client) {
        localStorage.setItem('peerflow_user', JSON.stringify(userData));
      }
    },
    
    setTokens(accessToken: string, refreshToken: string) {
      this.access_token = accessToken;
      this.refresh_token = refreshToken;
      if (process.client) {
        localStorage.setItem('peerflow_access_token', accessToken);
        localStorage.setItem('peerflow_refresh_token', refreshToken);
      }
    },
    
    logout() {
      this.user = null;
      this.access_token = null;
      this.refresh_token = null;
      this.assignment = null;
      this.peerReview = null;
      this.assignmentSubmissions = [];
      if (process.client) {
        localStorage.removeItem('peerflow_user');
        localStorage.removeItem('peerflow_access_token');
        localStorage.removeItem('peerflow_refresh_token');
      }
    },
    
    isAuthenticated(): boolean {
      return this.user !== null && this.access_token !== null;
    },

    isTeacher(): boolean {
      return this.user?.role === 'Teacher';
    },

    isStudent(): boolean {
      return this.user?.role === 'Student';
    },

    fetchAssignment(baseurl: string, assignmentId: string, force: boolean = true) {
      if (!force && this.assignment && this.assignment.id === assignmentId) {
        return Promise.resolve(this.assignment);
      }

      return axios.get(`${baseurl}/api/v1/assignments/${assignmentId}`, {
        headers: {
          'Authorization': `Bearer ${this.access_token}`,
          'Content-Type': 'application/json'
        }
      })
        .then(response => {
          console.log("Fetched assignment:", response.data);
          this.assignment = response.data.assignment;
          this.peerReview = response.data.peerReviewAssignment || null;
          this.assignmentSubmissions = response.data.submissions || [];
        });
    }

  },
  
  getters: {
    userName: (state) => state.user?.name,
    userRole: (state) => state.user?.role
  }
});