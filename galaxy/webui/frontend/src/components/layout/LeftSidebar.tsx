import React from 'react';
import SessionControlBar from '../session/SessionControlBar';
import DevicePanel from '../devices/DevicePanel';

const LeftSidebar: React.FC = () => {
  return (
    <div className="flex h-full w-full flex-col gap-4 overflow-hidden">
      <SessionControlBar />
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        <DevicePanel />
      </div>
    </div>
  );
};

export default LeftSidebar;
