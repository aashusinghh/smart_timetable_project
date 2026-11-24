import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export const Layout: React.FC = () => {
  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 print:bg-white print:text-black">
      <div className="print:hidden">
        <Sidebar />
      </div>
      <div className="flex-1 flex flex-col min-w-0 print:bg-white print:text-black">
        <div className="print:hidden">
          <Topbar />
        </div>
        <main className="flex-1 p-6 lg:p-8 print:p-0 print:m-0 overflow-y-auto print:overflow-visible print:bg-white print:text-black">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

