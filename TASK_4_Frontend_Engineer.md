# 🎨 LogGuard — Person 4: Frontend Engineer
## Role: React Dashboard & UI/UX Lead

---

## 📌 Your Responsibility Summary

Tum LogGuard ka "chehra" ho. Chahe backend aur ML kitne bhi acche kaam karein — agar dashboard usable nahi hai, product bikta nahi. Tumhara kaam hai ek **enterprise-grade, real-time AIOps dashboard** banana jo:

- Real-time anomaly alerts WebSocket se receive kare aur dikhaye
- Anomaly timeline charts render kare (host-level aur fleet-level)
- Root Cause Analysis panels mein log analysis dikhaye
- Alert rule configuration UI banana
- ML feedback buttons ("True Positive / False Positive") integrate karo
- Fast, accessible, aur dark-mode compatible ho

**Tumhara kaam directly end-customer ko dikhta hai. Quality bar sabse upar hai.**

---

## 🧰 Tech Stack (Tumhara Arsenal)

| Technology | Purpose | Seekhne ki zaroorat |
|---|---|---|
| **React 18 + TypeScript** | Primary UI framework | High ⭐⭐⭐ |
| **TanStack Query v5** | Server state, caching, refetching | High ⭐⭐⭐ |
| **Zustand** | Lightweight UI/client state | Medium ⭐⭐ |
| **React Router v6** | Client-side routing | Medium ⭐⭐ |
| **Tailwind CSS v3** | Utility-first styling | High ⭐⭐⭐ |
| **Apache ECharts / Recharts** | Anomaly timeline charts | High ⭐⭐⭐ |
| **TanStack Table** | Virtual log table (millions of rows) | Medium ⭐⭐ |
| **WebSocket (native)** | Real-time anomaly streaming | Medium ⭐⭐ |
| **Axios** | HTTP requests to FastAPI | Low ⭐ |
| **Radix UI** | Accessible headless components | Medium ⭐⭐ |
| **Vitest + Testing Library** | Unit + component tests | Medium ⭐⭐ |
| **Storybook** | Component development in isolation | Low ⭐ |
| **Vite** | Build tool | Low ⭐ |

---

## 📁 Folder Structure (Tumhara Code)

```
logguard/
└── frontend/
    ├── public/
    │   └── favicon.svg
    │
    ├── src/
    │   ├── main.tsx                        ← App entry point
    │   ├── App.tsx                         ← Router setup
    │   │
    │   ├── pages/
    │   │   ├── Dashboard.tsx               ← Main anomaly overview
    │   │   ├── HostDetail.tsx              ← Single host drill-down + RCA
    │   │   ├── LogExplorer.tsx             ← Full-text log search page
    │   │   ├── AlertRules.tsx              ← Alert configuration CRUD
    │   │   ├── Incidents.tsx               ← Correlated incident list
    │   │   └── Settings.tsx                ← User + integration settings
    │   │
    │   ├── components/
    │   │   ├── layout/
    │   │   │   ├── Sidebar.tsx
    │   │   │   ├── TopBar.tsx
    │   │   │   └── PageShell.tsx
    │   │   ├── anomaly/
    │   │   │   ├── AnomalyTimeline.tsx     ← ECharts time-series chart
    │   │   │   ├── AnomalyTable.tsx        ← Virtualized anomaly list
    │   │   │   ├── AnomalyCard.tsx         ← Single anomaly detail card
    │   │   │   ├── AnomalyFeedback.tsx     ← TP/FP feedback buttons
    │   │   │   └── ScoreBadge.tsx          ← Color-coded score badge
    │   │   ├── rca/
    │   │   │   ├── RcaPanel.tsx            ← Root cause analysis view
    │   │   │   └── TemplateList.tsx        ← Contributing log templates
    │   │   ├── hosts/
    │   │   │   ├── HostGrid.tsx            ← Fleet status grid
    │   │   │   └── HostStatusCard.tsx      ← Per-host health card
    │   │   ├── alerts/
    │   │   │   ├── AlertRuleForm.tsx       ← Create/edit alert rule
    │   │   │   └── AlertRuleCard.tsx
    │   │   ├── realtime/
    │   │   │   └── LiveFeed.tsx            ← Real-time anomaly notification feed
    │   │   └── ui/                         ← Design system primitives
    │   │       ├── Badge.tsx
    │   │       ├── Button.tsx
    │   │       ├── Card.tsx
    │   │       ├── DataTable.tsx
    │   │       ├── Modal.tsx
    │   │       ├── Skeleton.tsx
    │   │       └── Tooltip.tsx
    │   │
    │   ├── hooks/
    │   │   ├── useAnomalies.ts             ← TanStack Query: anomaly data
    │   │   ├── useHosts.ts                 ← Host stats query
    │   │   ├── useWebSocket.ts             ← WebSocket connection + events
    │   │   ├── useAlertRules.ts            ← Alert CRUD mutations
    │   │   └── useFeedback.ts              ← Submit feedback mutation
    │   │
    │   ├── store/
    │   │   ├── useUIStore.ts               ← Sidebar, theme, filters (Zustand)
    │   │   └── useLiveFeedStore.ts         ← Real-time anomaly buffer (Zustand)
    │   │
    │   ├── api/
    │   │   ├── client.ts                   ← Axios instance + interceptors
    │   │   ├── anomalies.ts                ← API functions for anomaly endpoints
    │   │   ├── logs.ts
    │   │   ├── alerts.ts
    │   │   └── feedback.ts
    │   │
    │   ├── types/
    │   │   ├── anomaly.ts                  ← TypeScript interfaces
    │   │   ├── alert.ts
    │   │   └── host.ts
    │   │
    │   └── utils/
    │       ├── formatScore.ts              ← Score → color/label helpers
    │       ├── formatTime.ts               ← Relative/absolute time formatting
    │       └── constants.ts
    │
    ├── tests/
    │   ├── AnomalyTimeline.test.tsx
    │   ├── AnomalyFeedback.test.tsx
    │   └── useWebSocket.test.ts
    │
    ├── index.html
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    └── package.json
```

---

## 🚀 Phase 1: Project Setup + Design System (Week 13)

### Step 1.1 — Vite + React + TypeScript

```bash
# Create project
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install all dependencies
npm install \
  @tanstack/react-query@5 \
  @tanstack/react-table@8 \
  @tanstack/react-virtual@3 \
  zustand \
  react-router-dom@6 \
  axios \
  echarts \
  echarts-for-react \
  @radix-ui/react-dialog \
  @radix-ui/react-dropdown-menu \
  @radix-ui/react-tooltip \
  @radix-ui/react-switch \
  @radix-ui/react-select \
  date-fns \
  clsx \
  tailwind-merge

npm install -D \
  tailwindcss \
  postcss \
  autoprefixer \
  @types/node \
  vitest \
  @testing-library/react \
  @testing-library/user-event \
  jsdom

npx tailwindcss init -p
```

### Step 1.2 — Tailwind Config

`tailwind.config.ts`:
```typescript
import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // LogGuard brand palette
        brand: {
          50:  '#EEF2FF',
          100: '#E0E7FF',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          900: '#312E81',
        },
        anomaly: {
          critical: '#EF4444',  // score > 0.9
          high:     '#F97316',  // score 0.8–0.9
          medium:   '#EAB308',  // score 0.7–0.8
          low:      '#22C55E',  // score < 0.7
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-fast': 'pulse 0.8s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'slide-in':   'slideIn 0.2s ease-out',
        'fade-in':    'fadeIn 0.15s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%':   { transform: 'translateY(-8px)', opacity: '0' },
          '100%': { transform: 'translateY(0)',     opacity: '1' },
        },
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
      }
    },
  },
  plugins: [],
} satisfies Config
```

### Step 1.3 — TypeScript Types

`src/types/anomaly.ts`:
```typescript
export interface AnomalyScore {
  id: number
  scored_at: string           // ISO timestamp
  host: string
  tenant_id: string
  final_score: number         // 0–1, higher = more anomalous
  if_score: number            // Isolation Forest contribution
  lstm_score: number          // LSTM contribution
  is_anomaly: boolean
  anomaly_type: string | null
  log_volume: number | null
  error_rate: number | null   // 0–1
  feature_window_start: string | null
  feature_window_end: string | null
}

export interface AnomalyTimelineBucket {
  bucket: string              // ISO timestamp of bucket start
  host: string
  avg_score: number
  max_score: number
  window_count: number
  anomaly_count: number
}

export interface RcaResult {
  anomaly_id: number
  window_start: string
  window_end: string
  host: string
  contributing_templates: ContributingTemplate[]
  unusual_log_count: number
  total_log_count: number
}

export interface ContributingTemplate {
  template: string
  template_id: string
  baseline_rate: number       // Normal occurrence rate
  anomaly_rate: number        // Rate during anomaly window
  lift: number                // anomaly_rate / baseline_rate
  example_log: string | null
}

export type FeedbackType = 'true_positive' | 'false_positive'

export interface FeedbackPayload {
  anomaly_id: number
  scored_at: string
  host: string
  feedback_type: FeedbackType
  notes?: string
}

export type AnomalySeverity = 'critical' | 'high' | 'medium' | 'normal'

export function getAnomalySeverity(score: number): AnomalySeverity {
  if (score >= 0.9) return 'critical'
  if (score >= 0.8) return 'high'
  if (score >= 0.7) return 'medium'
  return 'normal'
}

export const SEVERITY_COLORS: Record<AnomalySeverity, string> = {
  critical: 'text-red-500 bg-red-50 border-red-200',
  high:     'text-orange-500 bg-orange-50 border-orange-200',
  medium:   'text-yellow-600 bg-yellow-50 border-yellow-200',
  normal:   'text-green-600 bg-green-50 border-green-200',
}

export const SEVERITY_DOT: Record<AnomalySeverity, string> = {
  critical: 'bg-red-500 animate-pulse-fast',
  high:     'bg-orange-500 animate-pulse',
  medium:   'bg-yellow-500',
  normal:   'bg-green-500',
}
```

`src/types/alert.ts`:
```typescript
export type NotifierType = 'slack' | 'pagerduty' | 'email'
export type AlertSeverity = 'low' | 'medium' | 'high' | 'critical'

export interface AlertRule {
  id: string
  name: string
  description: string | null
  host_pattern: string | null   // e.g. "web-*" or null for all
  score_threshold: number       // 0–1
  severity: AlertSeverity
  notifier_type: NotifierType
  notifier_config: Record<string, string>
  cooldown_minutes: number
  is_active: boolean
  created_at: string
}

export interface AlertRuleFormValues {
  name: string
  description: string
  host_pattern: string
  score_threshold: number
  severity: AlertSeverity
  notifier_type: NotifierType
  webhook_url?: string          // For Slack
  integration_key?: string      // For PagerDuty
  email_addresses?: string      // Comma-separated for Email
  cooldown_minutes: number
}
```

---

## 🚀 Phase 2: API Client + Hooks (Week 13–14)

### Step 2.1 — Axios Client

`src/api/client.ts`:
```typescript
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 10_000,
})

// Attach JWT token to every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('logguard_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Global error handling
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('logguard_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

`src/api/anomalies.ts`:
```typescript
import { apiClient } from './client'
import type { AnomalyScore, AnomalyTimelineBucket, RcaResult } from '../types/anomaly'

export interface AnomalyListParams {
  host?: string
  from_time?: string
  to_time?: string
  min_score?: number
  limit?: number
}

export const anomaliesApi = {
  list: async (params: AnomalyListParams): Promise<{ anomalies: AnomalyScore[]; count: number }> => {
    const { data } = await apiClient.get('/anomalies/', { params })
    return data
  },

  timeline: async (params: {
    host?: string
    bucket_minutes?: number
    hours_back?: number
  }): Promise<{ timeline: AnomalyTimelineBucket[] }> => {
    const { data } = await apiClient.get('/anomalies/timeline', { params })
    return data
  },

  getRca: async (anomalyId: number): Promise<{ anomaly_id: number; rca: RcaResult }> => {
    const { data } = await apiClient.get(`/anomalies/${anomalyId}/rca`)
    return data
  },
}
```

### Step 2.2 — TanStack Query Hooks

`src/hooks/useAnomalies.ts`:
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { anomaliesApi, type AnomalyListParams } from '../api/anomalies'
import { feedbackApi } from '../api/feedback'
import type { FeedbackPayload } from '../types/anomaly'

// Anomaly list with auto-refresh every 30 seconds
export function useAnomalies(params: AnomalyListParams) {
  return useQuery({
    queryKey: ['anomalies', params],
    queryFn: () => anomaliesApi.list(params),
    refetchInterval: 30_000,    // Re-fetch every 30s for non-WS updates
    staleTime: 15_000,
    select: (data) => data.anomalies,
  })
}

// Timeline data for charts
export function useAnomalyTimeline(host?: string, hoursBack: number = 24) {
  return useQuery({
    queryKey: ['anomaly-timeline', host, hoursBack],
    queryFn: () => anomaliesApi.timeline({ host, hours_back: hoursBack, bucket_minutes: 5 }),
    refetchInterval: 60_000,
    select: (data) => data.timeline,
  })
}

// RCA data — only fetch when user clicks "View RCA"
export function useRca(anomalyId: number | null) {
  return useQuery({
    queryKey: ['rca', anomalyId],
    queryFn: () => anomaliesApi.getRca(anomalyId!),
    enabled: anomalyId !== null,
    staleTime: 5 * 60_000,      // RCA doesn't change — cache for 5 min
    select: (data) => data.rca,
  })
}

// Feedback mutation
export function useFeedback() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (payload: FeedbackPayload) => feedbackApi.submit(payload),
    onSuccess: (_, variables) => {
      // Invalidate anomaly list so UI can update state
      queryClient.invalidateQueries({ queryKey: ['anomalies'] })
      console.log(`✅ Feedback submitted: ${variables.feedback_type} for anomaly ${variables.anomaly_id}`)
    },
  })
}
```

### Step 2.3 — WebSocket Hook

`src/hooks/useWebSocket.ts`:
```typescript
import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useLiveFeedStore } from '../store/useLiveFeedStore'
import type { AnomalyScore } from '../types/anomaly'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/anomalies'
const RECONNECT_DELAY_MS = 3000
const MAX_RECONNECT_ATTEMPTS = 10

export function useWebSocket() {
  const ws            = useRef<WebSocket | null>(null)
  const reconnectRef  = useRef<ReturnType<typeof setTimeout>>()
  const attemptsRef   = useRef(0)
  
  const queryClient   = useQueryClient()
  const { addAnomaly, setConnected } = useLiveFeedStore()
  
  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return
    
    const socket = new WebSocket(WS_URL)
    
    socket.onopen = () => {
      console.log('🟢 WebSocket connected')
      setConnected(true)
      attemptsRef.current = 0
    }
    
    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        
        if (msg.type === 'anomaly') {
          const anomaly = msg.data as AnomalyScore
          
          // 1. Add to real-time live feed (Zustand store)
          addAnomaly(anomaly)
          
          // 2. Invalidate TanStack Query cache so tables auto-update
          queryClient.invalidateQueries({ queryKey: ['anomalies'] })
          queryClient.invalidateQueries({ queryKey: ['anomaly-timeline'] })
          
          // 3. Browser notification if tab is in background
          if (document.visibilityState === 'hidden' && anomaly.final_score >= 0.85) {
            new Notification('LogGuard Alert', {
              body: `High anomaly on ${anomaly.host} (score: ${Math.round(anomaly.final_score * 100)}%)`,
              icon: '/favicon.svg',
            })
          }
        }
        
        if (event.data === 'ping') {
          socket.send('pong')
        }
      } catch (e) {
        console.error('WS message parse error:', e)
      }
    }
    
    socket.onclose = () => {
      setConnected(false)
      console.warn('🔴 WebSocket disconnected')
      
      if (attemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        attemptsRef.current++
        console.log(`Reconnecting in ${RECONNECT_DELAY_MS}ms (attempt ${attemptsRef.current})...`)
        reconnectRef.current = setTimeout(connect, RECONNECT_DELAY_MS)
      }
    }
    
    socket.onerror = (err) => {
      console.error('WebSocket error:', err)
      socket.close()
    }
    
    ws.current = socket
  }, [queryClient, addAnomaly, setConnected])
  
  useEffect(() => {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
    
    connect()
    
    return () => {
      clearTimeout(reconnectRef.current)
      ws.current?.close()
    }
  }, [connect])
}
```

### Step 2.4 — Zustand Store

`src/store/useLiveFeedStore.ts`:
```typescript
import { create } from 'zustand'
import type { AnomalyScore } from '../types/anomaly'

const MAX_FEED_SIZE = 100  // Keep last 100 real-time anomalies

interface LiveFeedStore {
  anomalies: AnomalyScore[]
  isConnected: boolean
  unreadCount: number
  addAnomaly: (anomaly: AnomalyScore) => void
  setConnected: (status: boolean) => void
  markAllRead: () => void
  clearFeed: () => void
}

export const useLiveFeedStore = create<LiveFeedStore>((set) => ({
  anomalies:    [],
  isConnected:  false,
  unreadCount:  0,
  
  addAnomaly: (anomaly) => set((state) => ({
    anomalies: [anomaly, ...state.anomalies].slice(0, MAX_FEED_SIZE),
    unreadCount: state.unreadCount + 1,
  })),
  
  setConnected: (isConnected) => set({ isConnected }),
  
  markAllRead: () => set({ unreadCount: 0 }),
  
  clearFeed: () => set({ anomalies: [], unreadCount: 0 }),
}))
```

---

## 🚀 Phase 3: Core Dashboard Components (Week 14–15)

### Step 3.1 — Anomaly Score Badge

`src/components/ui/ScoreBadge.tsx`:
```tsx
import { getAnomalySeverity, SEVERITY_COLORS } from '../../types/anomaly'
import { clsx } from 'clsx'

interface ScoreBadgeProps {
  score: number
  showLabel?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export function ScoreBadge({ score, showLabel = true, size = 'md' }: ScoreBadgeProps) {
  const severity    = getAnomalySeverity(score)
  const colorClass  = SEVERITY_COLORS[severity]
  const percentage  = Math.round(score * 100)
  
  const sizeClass = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  }[size]
  
  return (
    <span className={clsx(
      'inline-flex items-center gap-1.5 rounded-full border font-mono font-semibold',
      colorClass,
      sizeClass
    )}>
      <span className={clsx(
        'w-1.5 h-1.5 rounded-full',
        {
          'bg-red-500 animate-pulse-fast': severity === 'critical',
          'bg-orange-500 animate-pulse':   severity === 'high',
          'bg-yellow-500':                 severity === 'medium',
          'bg-green-500':                  severity === 'normal',
        }
      )} />
      {percentage}%
      {showLabel && <span className="font-sans font-normal capitalize ml-0.5">{severity}</span>}
    </span>
  )
}
```

### Step 3.2 — Anomaly Timeline Chart (ECharts)

`src/components/anomaly/AnomalyTimeline.tsx`:
```tsx
import ReactECharts from 'echarts-for-react'
import { useMemo } from 'react'
import { format } from 'date-fns'
import { useAnomalyTimeline } from '../../hooks/useAnomalies'
import { Skeleton } from '../ui/Skeleton'
import type { EChartsOption } from 'echarts'

interface AnomalyTimelineProps {
  host?: string
  hoursBack?: number
}

export function AnomalyTimeline({ host, hoursBack = 24 }: AnomalyTimelineProps) {
  const { data: timeline, isLoading } = useAnomalyTimeline(host, hoursBack)
  
  const chartOption: EChartsOption = useMemo(() => {
    if (!timeline?.length) return {}
    
    const times    = timeline.map(b => format(new Date(b.bucket), 'HH:mm'))
    const avgScores = timeline.map(b => +(b.avg_score * 100).toFixed(1))
    const maxScores = timeline.map(b => +(b.max_score * 100).toFixed(1))
    
    // Build anomaly markers (red dots where anomaly_count > 0)
    const markPoints = timeline
      .map((b, i) => b.anomaly_count > 0 ? {
        coord: [i, maxScores[i]],
        symbol: 'circle',
        symbolSize: 8,
        itemStyle: { color: '#EF4444' }
      } : null)
      .filter(Boolean)
    
    return {
      backgroundColor: 'transparent',
      grid: { top: 20, right: 20, bottom: 40, left: 50 },
      tooltip: {
        trigger: 'axis',
        backgroundColor: '#1e1e2e',
        borderColor: '#374151',
        textStyle: { color: '#e5e7eb' },
        formatter: (params: any) => {
          const i = params[0].dataIndex
          const b = timeline[i]
          return `
            <div class="p-2 text-sm">
              <div class="font-bold mb-1">${times[i]}</div>
              <div>Avg Score: <b>${avgScores[i]}%</b></div>
              <div>Max Score: <b>${maxScores[i]}%</b></div>
              <div>Anomalies: <b style="color:#EF4444">${b.anomaly_count}</b></div>
              <div>Log Volume: <b>${b.window_count}</b></div>
            </div>
          `
        }
      },
      xAxis: {
        type: 'category',
        data: times,
        axisLabel: { color: '#6b7280', fontSize: 11 },
        axisLine: { lineStyle: { color: '#374151' } },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: {
          color: '#6b7280',
          fontSize: 11,
          formatter: '{value}%'
        },
        splitLine: { lineStyle: { color: '#1f2937', type: 'dashed' } },
      },
      series: [
        {
          name: 'Average Score',
          type: 'line',
          data: avgScores,
          smooth: true,
          lineStyle: { color: '#6366f1', width: 2 },
          areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(99,102,241,0.3)' },
                { offset: 1, color: 'rgba(99,102,241,0.02)' }
              ]
            }
          },
          symbol: 'none',
          markPoint: { data: markPoints },
        },
        {
          name: 'Peak Score',
          type: 'line',
          data: maxScores,
          smooth: true,
          lineStyle: { color: '#EF4444', width: 1.5, type: 'dashed' },
          symbol: 'none',
        },
        // Threshold line at 70%
        {
          name: 'Threshold',
          type: 'line',
          markLine: {
            silent: true,
            symbol: 'none',
            data: [{ yAxis: 70 }],
            lineStyle: { color: '#F97316', type: 'dashed', width: 1 },
            label: { formatter: 'Threshold (70%)', color: '#F97316', fontSize: 11 }
          },
          data: [],
        }
      ]
    }
  }, [timeline])
  
  if (isLoading) return <Skeleton className="h-64 w-full rounded-xl" />
  
  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-200">
          Anomaly Score Timeline
          {host && <span className="ml-2 text-gray-400 font-mono">· {host}</span>}
        </h3>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-indigo-500 inline-block"/>Avg
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-0.5 bg-red-500 inline-block" style={{borderTop:'1px dashed'}}/>Peak
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-red-500 inline-block"/>Anomaly
          </span>
        </div>
      </div>
      <ReactECharts
        option={chartOption}
        style={{ height: '220px' }}
        opts={{ renderer: 'canvas' }}
        notMerge
      />
    </div>
  )
}
```

### Step 3.3 — Anomaly Feedback Component

`src/components/anomaly/AnomalyFeedback.tsx`:
```tsx
import { useState } from 'react'
import { ThumbsUp, ThumbsDown, Loader2 } from 'lucide-react'
import { useFeedback } from '../../hooks/useAnomalies'
import type { AnomalyScore, FeedbackType } from '../../types/anomaly'
import { clsx } from 'clsx'

interface AnomalyFeedbackProps {
  anomaly: AnomalyScore
}

export function AnomalyFeedback({ anomaly }: AnomalyFeedbackProps) {
  const [submitted, setSubmitted] = useState<FeedbackType | null>(null)
  const { mutate: submitFeedback, isPending } = useFeedback()
  
  const handleFeedback = (feedbackType: FeedbackType) => {
    submitFeedback({
      anomaly_id: anomaly.id,
      scored_at: anomaly.scored_at,
      host: anomaly.host,
      feedback_type: feedbackType,
    }, {
      onSuccess: () => setSubmitted(feedbackType)
    })
  }
  
  if (submitted) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <span className={submitted === 'true_positive' ? 'text-red-400' : 'text-green-400'}>
          {submitted === 'true_positive' ? '✓ Confirmed anomaly' : '✓ Marked false positive'}
        </span>
        <span className="text-gray-600 text-xs">· Thanks for training the model</span>
      </div>
    )
  }
  
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 mr-1">Is this correct?</span>
      
      {/* True Positive button */}
      <button
        onClick={() => handleFeedback('true_positive')}
        disabled={isPending}
        className={clsx(
          'flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all',
          'border-gray-700 text-gray-400 hover:border-red-500 hover:text-red-400 hover:bg-red-950/20',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
        title="This is a real anomaly (true positive)"
      >
        {isPending ? <Loader2 size={12} className="animate-spin" /> : <ThumbsDown size={12} />}
        Real anomaly
      </button>
      
      {/* False Positive button */}
      <button
        onClick={() => handleFeedback('false_positive')}
        disabled={isPending}
        className={clsx(
          'flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all',
          'border-gray-700 text-gray-400 hover:border-green-500 hover:text-green-400 hover:bg-green-950/20',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
        title="This was incorrectly flagged (false positive)"
      >
        {isPending ? <Loader2 size={12} className="animate-spin" /> : <ThumbsUp size={12} />}
        False alarm
      </button>
    </div>
  )
}
```

### Step 3.4 — RCA Panel

`src/components/rca/RcaPanel.tsx`:
```tsx
import { useRca } from '../../hooks/useAnomalies'
import { Skeleton } from '../ui/Skeleton'

interface RcaPanelProps {
  anomalyId: number
  host: string
}

export function RcaPanel({ anomalyId, host }: RcaPanelProps) {
  const { data: rca, isLoading, isError } = useRca(anomalyId)
  
  if (isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-4 w-48" />
        {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
      </div>
    )
  }
  
  if (isError || !rca) {
    return <p className="text-sm text-gray-500">Could not load RCA data.</p>
  }
  
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200">Root Cause Analysis</h3>
        <span className="text-xs text-gray-500">
          {rca.unusual_log_count} unusual logs / {rca.total_log_count} total
        </span>
      </div>
      
      <p className="text-xs text-gray-400">
        Log templates with unusually high occurrence during this anomaly window on{' '}
        <code className="text-indigo-400">{host}</code>:
      </p>
      
      <div className="space-y-2">
        {rca.contributing_templates.map((t, i) => (
          <div
            key={t.template_id}
            className="bg-gray-800 rounded-lg p-3 border border-gray-700"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <p className="text-xs font-mono text-gray-300 truncate">
                  {t.template}
                </p>
                {t.example_log && (
                  <p className="text-xs text-gray-600 font-mono truncate mt-0.5">
                    {t.example_log}
                  </p>
                )}
              </div>
              
              {/* Lift indicator: how much more frequent than baseline */}
              <div className="shrink-0 text-right">
                <span className={`text-sm font-bold ${t.lift > 5 ? 'text-red-400' : t.lift > 2 ? 'text-orange-400' : 'text-yellow-400'}`}>
                  {t.lift.toFixed(1)}×
                </span>
                <p className="text-xs text-gray-600">frequency lift</p>
              </div>
            </div>
            
            {/* Frequency comparison bar */}
            <div className="mt-2 flex items-center gap-2">
              <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 rounded-full transition-all"
                  style={{ width: `${Math.min(t.anomaly_rate * 100, 100)}%` }}
                />
              </div>
              <span className="text-xs text-gray-500 w-24 text-right">
                {(t.anomaly_rate * 100).toFixed(1)}% vs {(t.baseline_rate * 100).toFixed(1)}% baseline
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

### Step 3.5 — Live Feed Sidebar

`src/components/realtime/LiveFeed.tsx`:
```tsx
import { useLiveFeedStore } from '../../store/useLiveFeedStore'
import { ScoreBadge } from '../ui/ScoreBadge'
import { formatDistanceToNow } from 'date-fns'
import { Wifi, WifiOff, X } from 'lucide-react'
import { clsx } from 'clsx'

export function LiveFeed() {
  const { anomalies, isConnected, unreadCount, markAllRead, clearFeed } = useLiveFeedStore()
  
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-800">
        <div className="flex items-center gap-2">
          {isConnected
            ? <Wifi size={14} className="text-green-400" />
            : <WifiOff size={14} className="text-red-400 animate-pulse" />
          }
          <span className="text-sm font-semibold text-gray-200">Live Feed</span>
          {unreadCount > 0 && (
            <span className="bg-red-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
              {unreadCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          {unreadCount > 0 && (
            <button
              onClick={markAllRead}
              className="text-xs text-gray-500 hover:text-gray-300 px-2 py-1"
            >
              Mark read
            </button>
          )}
          <button
            onClick={clearFeed}
            className="text-gray-600 hover:text-gray-400 p-1"
          >
            <X size={12} />
          </button>
        </div>
      </div>
      
      {/* Feed items */}
      <div className="flex-1 overflow-y-auto divide-y divide-gray-800/50">
        {anomalies.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-600">
            <Wifi size={20} className="mb-2 opacity-50" />
            <p className="text-xs">Watching for anomalies...</p>
          </div>
        ) : (
          anomalies.map((anomaly, i) => (
            <div
              key={`${anomaly.id}-${anomaly.scored_at}`}
              className={clsx(
                'p-3 hover:bg-gray-800/50 transition-colors cursor-pointer',
                'animate-fade-in',
                i === 0 && 'bg-gray-800/30'  // Highlight newest
              )}
            >
              <div className="flex items-center justify-between mb-1">
                <code className="text-xs text-indigo-400 font-mono">{anomaly.host}</code>
                <ScoreBadge score={anomaly.final_score} size="sm" showLabel={false} />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  {anomaly.error_rate !== null && (
                    <span className="text-red-400">{(anomaly.error_rate * 100).toFixed(1)}% errors</span>
                  )}
                </span>
                <span className="text-xs text-gray-600">
                  {formatDistanceToNow(new Date(anomaly.scored_at), { addSuffix: true })}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
```

---

## 🚀 Phase 4: Dashboard Page Assembly (Week 15–16)

### Step 4.1 — Main Dashboard

`src/pages/Dashboard.tsx`:
```tsx
import { useEffect } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAnomalies, useAnomalyTimeline } from '../hooks/useAnomalies'
import { AnomalyTimeline } from '../components/anomaly/AnomalyTimeline'
import { AnomalyTable } from '../components/anomaly/AnomalyTable'
import { HostGrid } from '../components/hosts/HostGrid'
import { LiveFeed } from '../components/realtime/LiveFeed'
import { PageShell } from '../components/layout/PageShell'
import { useLiveFeedStore } from '../store/useLiveFeedStore'

export function Dashboard() {
  // Initialize WebSocket on dashboard mount
  useWebSocket()
  
  const { isConnected, unreadCount } = useLiveFeedStore()
  
  const { data: recentAnomalies, isLoading } = useAnomalies({
    min_score: 0.70,
    limit: 50,
  })
  
  return (
    <PageShell title="Overview Dashboard">
      {/* Top stats row */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard
          label="Active Anomalies"
          value={recentAnomalies?.filter(a => a.is_anomaly).length ?? 0}
          color="red"
        />
        <StatCard
          label="Hosts Monitored"
          value={new Set(recentAnomalies?.map(a => a.host)).size ?? 0}
          color="blue"
        />
        <StatCard
          label="Avg Score (24h)"
          value={
            recentAnomalies?.length
              ? `${Math.round((recentAnomalies.reduce((s,a) => s+a.final_score,0) / recentAnomalies.length) * 100)}%`
              : '—'
          }
          color="indigo"
        />
        <StatCard
          label="WebSocket"
          value={isConnected ? 'Connected' : 'Reconnecting...'}
          color={isConnected ? 'green' : 'red'}
        />
      </div>
      
      {/* Main grid */}
      <div className="grid grid-cols-12 gap-4">
        {/* Timeline chart — full width */}
        <div className="col-span-12">
          <AnomalyTimeline hoursBack={24} />
        </div>
        
        {/* Anomaly table */}
        <div className="col-span-8">
          <AnomalyTable anomalies={recentAnomalies ?? []} isLoading={isLoading} />
        </div>
        
        {/* Live feed sidebar */}
        <div className="col-span-4 bg-gray-900 rounded-xl border border-gray-800" style={{ height: '520px' }}>
          <LiveFeed />
        </div>
        
        {/* Host health grid */}
        <div className="col-span-12">
          <HostGrid />
        </div>
      </div>
    </PageShell>
  )
}

function StatCard({ label, value, color }: { label: string; value: any; color: string }) {
  const colorMap = {
    red: 'border-red-800 bg-red-950/20 text-red-400',
    blue: 'border-blue-800 bg-blue-950/20 text-blue-400',
    indigo: 'border-indigo-800 bg-indigo-950/20 text-indigo-400',
    green: 'border-green-800 bg-green-950/20 text-green-400',
  }
  
  return (
    <div className={`rounded-xl border p-4 ${colorMap[color as keyof typeof colorMap]}`}>
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className="text-2xl font-bold font-mono">{value}</p>
    </div>
  )
}
```

---

## 🧪 Testing Guide

```bash
# Unit tests
npm run test

# Watch mode
npm run test -- --watch

# Coverage report
npm run test -- --coverage
```

`tests/AnomalyFeedback.test.tsx`:
```tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AnomalyFeedback } from '../src/components/anomaly/AnomalyFeedback'
import { vi } from 'vitest'

// Mock the feedback API
vi.mock('../src/api/feedback', () => ({
  feedbackApi: {
    submit: vi.fn().mockResolvedValue({ status: 'recorded' })
  }
}))

const mockAnomaly = {
  id: 123, scored_at: '2024-01-15T14:00:00Z',
  host: 'web-01', tenant_id: 't1',
  final_score: 0.85, if_score: 0.7, lstm_score: 0.9,
  is_anomaly: true, anomaly_type: null,
  log_volume: 500, error_rate: 0.15,
  feature_window_start: null, feature_window_end: null
}

function setup() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <AnomalyFeedback anomaly={mockAnomaly} />
    </QueryClientProvider>
  )
}

test('renders feedback buttons', () => {
  setup()
  expect(screen.getByText('Real anomaly')).toBeInTheDocument()
  expect(screen.getByText('False alarm')).toBeInTheDocument()
})

test('shows confirmation after feedback', async () => {
  setup()
  fireEvent.click(screen.getByText('False alarm'))
  await waitFor(() => {
    expect(screen.getByText(/Marked false positive/i)).toBeInTheDocument()
  })
})
```

---

## ✅ Deliverables / Checkpoints

### Week 13 Checkpoint
- [ ] Vite project setup, Tailwind dark mode working
- [ ] API client + all TypeScript types defined
- [ ] `ScoreBadge` component Storybook mein dikhna chahiye

### Week 14 Checkpoint
- [ ] `useWebSocket` hook working (test with mock WS server)
- [ ] `useLiveFeedStore` Zustand correctly buffer kare
- [ ] All TanStack Query hooks unit tested

### Week 15 Checkpoint
- [ ] `AnomalyTimeline` chart live data pe render ho raha ho
- [ ] `AnomalyFeedback` component submit kare aur confirmation dikhaye
- [ ] `RcaPanel` contributing templates dikhaye

### Week 16 Checkpoint
- [ ] Complete dashboard page assembled aur working
- [ ] `AlertRuleForm` create/edit functionality working
- [ ] Component tests 75%+ coverage

---

## 🤝 Dependencies on Other Team Members

| Dependency | Kya chahiye | Kisse lo |
|---|---|---|
| API base URL + endpoints | Backend API contract | Person 3 |
| WebSocket message format | `{type, data}` schema | Person 3 |
| JWT token format | Auth header format | Person 3 |
| Anomaly score fields | All field names in response | Person 3 |

---

## 📊 Performance Targets

| Metric | Target |
|---|---|
| Initial page load (LCP) | ≤ 2.5 seconds |
| Chart render time | ≤ 500ms |
| WebSocket reconnect time | ≤ 3 seconds |
| Log table virtual scroll | 100,000+ rows without lag |
| Lighthouse Performance score | ≥ 85 |
| Bundle size (gzipped) | ≤ 500KB |

---

## 📚 Resources to Study

1. **TanStack Query v5 Docs**: https://tanstack.com/query/latest
2. **Zustand Docs**: https://zustand-demo.pmnd.rs/
3. **Apache ECharts React**: https://echarts.apache.org/en/api.html
4. **Radix UI Components**: https://www.radix-ui.com/
5. **Tailwind CSS**: https://tailwindcss.com/docs
6. **React Testing Library**: https://testing-library.com/react

---

*LogGuard Frontend Engineer Task File — v1.0*  
*Har sprint mein Person 3 (Backend) se API contract confirm karte raho. Breaking changes se bachao.*
