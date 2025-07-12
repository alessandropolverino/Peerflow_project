<template>
  <v-row >

    <v-col cols="12" v-if="assignment.status == 'Open Submission'">
      <v-btn color="warning" @click="closeSubmission" class="mb-2">
        Close submission
      </v-btn>
    </v-col>

    

    <!-- Button to create or view peer reviews -->
    <v-col cols="12" v-if="peerReview == null && assignmentSubmissions.length > 0 && assignment?.status != 'Open Submission'">
      <v-btn :to="`/assignments/${route.params.id}/peer-review/create`" color="primary" class="mb-2">
        Create Peer Review
      </v-btn>
    </v-col>

    <v-col cols="5" v-if="peerReview == null && assignmentSubmissions.length == 0 && assignment?.status != 'Open Submission'">
      <v-btn color="grey" class="mb-2" disabled>
        Cannot create Peer Review (0 submissions)
      </v-btn>
    </v-col>

    <v-col cols="3" v-if="assignment.status == 'Closed Submission'">
      <v-menu
        v-model="menu"
        :close-on-content-click="false"
        transition="scale-transition"
        offset-y
        max-width="290px"
        min-width="290px"
      >
        <template v-slot:activator="{ props }">
          <v-btn color="primary" v-bind="props" class="mb-2">
            Reopen Submission
          </v-btn>
        </template>
        <v-card>
          <v-card-title>Select New Deadline</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="newDeadline"
              variant="outlined"
              hide-details="auto"
              color="primary"
              type="datetime-local"
              :rules="deadlineRules"
            ></v-text-field>
          </v-card-text>
          <v-card-actions>
            <v-btn text color="primary" @click="menu = false">Cancel</v-btn>
            <v-btn
              text
              color="primary"
              :disabled="!newDeadline || deadlineRules.some(rule => rule(newDeadline || '') !== true)"
              @click="reopenSubmission"
            >
              Confirm
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-menu>
    </v-col>

    <v-col cols="3" v-if="peerReview != null && assignment?.status != 'Open Submission'">
      <v-btn :to="`/assignments/${route.params.id}/peer-review`" color="primary" class="mb-2">
        View Peer Reviews
      </v-btn>
    </v-col>

    <!-- Students Accordion -->
    <v-col cols="12">
      <v-accordion>
        <v-accordion-item title="Involved Students">
          <v-text-field
            v-model="searchQuery"
            variant="outlined"
            hide-details="auto"
            color="primary"
            placeholder="Search students by name or email"
            class="mb-4"
          />

          <div class="selected-students-container">
            <v-list>
              <v-list-item
                v-for="student in filteredStudents"
                :key="student.id"
                class="border mb-2 rounded"
              >
                <template v-slot:prepend>
                  <v-avatar color="primary" size="40">
                    {{ student.name.charAt(0).toUpperCase() }}
                  </v-avatar>
                </template>

                <v-list-item-title>{{ student.name }}</v-list-item-title>
                <v-list-item-subtitle>{{ student.email }}</v-list-item-subtitle>

                <template v-slot:append>
                  <v-btn
                    v-if="assignmentSubmissions.some((submission:any) => submission.StudentID === student.id)"
                    :to="`/assignments/${route.params.id}/submission/${assignmentSubmissions.find((submission:any) => submission.StudentID === student.id).id}`"
                    color="primary"
                    small
                  >
                    View Submission
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </div>
        </v-accordion-item>
      </v-accordion>
    </v-col>


    <v-col cols="12">

      <div v-if="results.resultsBySubmission || ( results.resultsByReview && results.resultsByReview.length > 0)" class="mb-5">
        <h2 class="text-3xl my-5">Peer Review Results</h2>


        <div v-if="results.resultsBySubmission">
          <h5 class="text-h6 my-3">Results per each submission</h5>

          <div 
            v-for="submission in results.resultsBySubmission" :key="submission.SubmissionID" 
            class="border-left-grey mb-4 pl-4 mb-2"
            style="border-left: 2px solid grey;"
          >
            <h5 class="text-h6">Submission by: {{ getSubmitterStudentStringFromId(submission.SubmissionID) }}</h5>
            <v-table class="ma-2">
            <thead>
              <th># of Assigned Reviews</th>
              <th># of Completed Reviews</th>
              <th>Overall Average Score</th>
            </thead>
            <tbody>
              <tr>
                <td>{{ submission.NumberOfAssignedReviews }}</td>
                <td>{{ submission.NumberOfCompletedReviews }}</td>
                <td>{{ submission.OverallAverageScore }}</td>
              </tr>
            </tbody>
          </v-table>

          <p>Criterion Scores</p>
          <v-table>
            <thead>
              <tr>
                <th>Criterion</th>
                <th>Average Score</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(score, criterion) in submission.PerCriterionAverageScores" :key="criterion">
                <td>{{ criterion }}</td>
                <td>{{ score }}</td>
              </tr>
            </tbody>
          </v-table>
          </div>

          <!-- <h5 class="text-h6 my-3">Results per each submission</h5>
          <p>Overall Average Score: {{ results.resultsBySubmission.OverallAverageScore }}</p>

          <h5 class="text-h6 my-3">Criterion Scores</h5>
          <v-table>
            <thead>
              <tr>
                <th>Criterion</th>
                <th>Average Score</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(score, criterion) in results.resultsBySubmission.PerCriterionAverageScores" :key="criterion">
                <td>{{ criterion }}</td>
                <td>{{ score }}</td>
              </tr>
            </tbody>
          </v-table> -->
        </div>

        <div v-if="results.resultsByReview && results.resultsByReview.length > 0">
          <h5 class="text-h6 my-3">Average score of each review</h5>
          <v-table>
            <thead>
              <tr>
                <th>Review #</th>
                <th>Reviewee Submission</th>
                <th>Reviewer Student ID</th>
                <th>Overall Average Score</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(review, index) in results.resultsByReview" :key="review.RevieweeSubmissionID">

                <td>{{ index+1 }}</td>
                <td>{{ review.RevieweeSubmissionID }}</td>
                <td>{{ review.ReviewerStudentID }}</td>
                <td>{{ review.OverallAverageScore }}</td>
              </tr>
            </tbody>
          </v-table>
        </div>
      </div>

    </v-col>

  </v-row>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useGlobalStore } from '@/stores/globalStore';
import { storeToRefs } from 'pinia';
import axios from 'axios';

const config = useRuntimeConfig() 
// @ts-ignore
const PEERFLOW_API_URL = config.public.peerflowApiUrl;

const route = useRoute();
const globalStore = useGlobalStore();
const { assignment, peerReview, assignmentSubmissions } = storeToRefs(globalStore);

const searchQuery = ref('');
const menu = ref(false);
const newDeadline = ref(null);

const deadlineRules = [
  (value: string) => !!value || 'Deadline is required',
  (value: string) => {
    const selectedDate = new Date(value);
    const now = new Date();
    return selectedDate > now || 'Deadline must be in the future';
  }
];

const filteredStudents = computed(() => {
  if (!assignment.value?.involvedStudents) return [];

  const studentsWithSubmissions = assignment.value.involvedStudents.filter((student: { id: string; name: string; email: string }) =>
    assignmentSubmissions.value.some((submission: { StudentID: string }) => submission.StudentID === student.id)
  );

  const studentsWithoutSubmissions = assignment.value.involvedStudents.filter((student: { id: string; name: string; email: string }) =>
    !assignmentSubmissions.value.some((submission: { StudentID: string }) => submission.StudentID === student.id)
  );

  return [
    ...studentsWithSubmissions,
    ...studentsWithoutSubmissions
  ].filter(student =>
    student.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
    student.email.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});


const getSubmitterStudentStringFromId = (submissionId: string) => {
  const submission = globalStore.assignmentSubmissions?.find((sub: any) => sub.id === submissionId);
  const userId = submission?.StudentID;
  const student = globalStore.assignment?.involvedStudents.find((s: any) => s.id === userId);
  return student ? `${student.name} <${student.email}>` : 'Unknown Submitter';
};


interface ResBySubmission {
  SubmissionID: string;
  NumberOfAssignedReviews: number;
  NumberOfCompletedReviews: number;
  OverallAverageScore: number;
  PerCriterionAverageScores: Record<string, number>; // criterion name: average score
}

interface ResByReview {
  RevieweeSubmissionID: string;
  ReviewerStudentID: string;
  OverallAverageScore: number;
}

interface ResByAssignment {
  AssignmentID: string;
  OverallAverageScore: number;
  PerCriterionAverageScores: Record<string, number>; // criterion name: average score
  ScoreDistribution: Record<string, Record<string, number>>; // criterion name: { score: number of students that received this score }
}

interface StudentResults {
  resultsBySubmission: ResBySubmission[] | null;
  resultsByReview: ResByReview[] | null;
  resultsByAssignment: ResByAssignment | null;
}

const results = ref<StudentResults>({
  resultsBySubmission: null,
  resultsByReview: null,
  resultsByAssignment: null
});

const fetchResults = () => {
  if (assignmentSubmissions.value.length > 0) {
    axios.get(`${PEERFLOW_API_URL}/api/v1/assignments/${assignment.value.id}/peer-review/results/teacher`, {
      headers: {
        'Authorization': `Bearer ${globalStore.access_token}`
      }
    }).then(response => {
      if (response.status === 200) {
        console.log("Peer review results fetched successfully:", response.data);
        results.value.resultsBySubmission = response.data.resultsBySubmission;
        results.value.resultsByReview = response.data.resultsByReview;
        results.value.resultsByAssignment = response.data.resultsByAssignment;
      } else {
        console.error('Error fetching peer review results:', response.status);
      }
    }).catch(err => {
      console.error('Error fetching peer review results:', err);
    });
  }
}

const closeSubmission = async () => {

  axios.patch(`${PEERFLOW_API_URL}/api/v1/assignments/${route.params.id}`, {
    submissonDeadline: new Date().toISOString(),
  }, {
    headers: {
      'Authorization': `Bearer ${globalStore.access_token}`
    }
  }).then(response => {
    if (response.status === 200) {
      console.log('response', response.data);
      setTimeout(() => {
        globalStore.fetchAssignment(PEERFLOW_API_URL, route.params.id, true);
      }, 1000);
    } else {
      console.error('Failed to close submission:', response.statusText);
    }
  }).catch(error => {
    console.error('Error closing submission:', error);
  });
}

const reopenSubmission = async () => {
  if (!newDeadline.value) return;

  axios.patch(`${PEERFLOW_API_URL}/api/v1/assignments/${route.params.id}`, {
    submissonDeadline: new Date(newDeadline.value).toISOString(),
  }, {
    headers: {
      'Authorization': `Bearer ${globalStore.access_token}`
    }
  }).then(response => {
    if (response.status === 200) {
      console.log('response', response.data);
      globalStore.fetchAssignment(PEERFLOW_API_URL, route.params.id, true);
      menu.value = false;
    } else {
      console.error('Failed to reopen submission:', response.statusText);
    }
  }).catch(error => {
    console.error('Error reopening submission:', error);
  });
};

watch(() => peerReview, (newValue) => {
  if (newValue != null) {
    fetchResults();
  }
});

onMounted(() => {
  fetchResults();
})
</script>

<style scoped>
.selected-students-container {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background-color: #fafafa;
}

.selected-students-container::-webkit-scrollbar {
  width: 6px;
}

.selected-students-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.selected-students-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.selected-students-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.selected-students-container {
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}
</style>
