import React, { Suspense } from 'react';
const AgentDashboard = React.lazy(() => import('../components/AgentDashboard'));

export default function AgentCommandCenter({ latestFrame, totalPeople, runtimePeople }) {
  return (
    <div style={{ height: '100%', position: 'relative' }}>
      <Suspense fallback={
        <div style={{ 
          height: '100%', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: 'var(--text-secondary)'
        }}>
          Initializing Agent Subsystems...
        </div>
      }>
        <div style={{ 
          height: '100%', 
          /* Override the fixed positioning of the original component */
          position: 'absolute',
          top: 0, left: 0, right: 0, bottom: 0,
        }}>
          {/* We pass a dummy onClose because it's no longer a modal */}
          <AgentDashboard 
            onClose={() => {}} 
            latestFrame={latestFrame}
            totalPeople={totalPeople}
            runtimePeople={runtimePeople}
          />
        </div>
      </Suspense>
    </div>
  );
}
