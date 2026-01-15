import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/router';
import { logoutUser } from '../lib/auth';
import { getToken } from '../lib/token';
import { SESSION_TIMEOUT, SESSION_WARNING_TIME } from '../lib/constants';

const SessionTimeout: React.FC = () => {
  const router = useRouter();
  const [isWarningOpen, setIsWarningOpen] = useState(false);
  const throttleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    console.log('SessionTimeout mounted');
    console.log('Timeout:', SESSION_TIMEOUT);
    console.log('Warning Time:', SESSION_WARNING_TIME);
  }, []);

  const getLastActivity = () => {
    if (typeof window === 'undefined') return Date.now();
    const stored = localStorage.getItem('lastActivity');
    return stored ? Number(stored) : Date.now();
  };

  const setLastActivity = (time: number) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('lastActivity', time.toString());
    }
  };

  const logout = useCallback(async () => {
    try {
        await logoutUser();
    } catch (error) {
        console.error("Logout failed", error);
    }
    router.push('/auth');
    setIsWarningOpen(false);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('lastActivity');
    }
  }, [router]);

  const checkTimeout = useCallback(() => {
    const token = getToken();
    console.log('Checking timeout... Token exists:', !!token);
    if (!token) return; // Don't check if not logged in

    const now = Date.now();
    const lastActivity = getLastActivity();
    const timeSinceLastActivity = now - lastActivity;
    
    console.log(`Time since activity: ${timeSinceLastActivity}ms. Timeout at: ${SESSION_TIMEOUT}ms. Warning at: ${SESSION_TIMEOUT - SESSION_WARNING_TIME}ms`);

    if (timeSinceLastActivity > SESSION_TIMEOUT) {
      console.log('Session timed out. Logging out...');
      logout();
    } else if (timeSinceLastActivity > SESSION_TIMEOUT - SESSION_WARNING_TIME) {
      if (!isWarningOpen) {
          console.log('Warning threshold reached. Opening modal.');
          setIsWarningOpen(true);
      }
    } else {
        if (isWarningOpen) {
            setIsWarningOpen(false);
        }
    }
  }, [logout, isWarningOpen]);

  useEffect(() => {
    if (typeof window !== 'undefined' && !localStorage.getItem('lastActivity')) {
        setLastActivity(Date.now());
    }

    const interval = setInterval(checkTimeout, 1000);
    return () => clearInterval(interval);
  }, [checkTimeout]);

  useEffect(() => {
    const events = ['mousemove', 'keydown', 'click', 'scroll'];
    const handleActivity = () => {
        if (!throttleTimer.current) {
            setLastActivity(Date.now());
            throttleTimer.current = setTimeout(() => {
                throttleTimer.current = null;
            }, 1000);
        }
    };

    events.forEach(event => window.addEventListener(event, handleActivity));
    return () => events.forEach(event => window.removeEventListener(event, handleActivity));
  }, []);

  const extendSession = () => {
    setLastActivity(Date.now());
    setIsWarningOpen(false);
  };

  if (!isWarningOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-gray-900 text-white p-6 rounded-lg shadow-lg max-w-sm w-full border border-gray-700">
        <h2 className="text-xl font-bold mb-4">Session Timeout Warning</h2>
        <p className="mb-6 text-gray-300">Your session is about to expire due to inactivity. Please choose to extend your session or log out.</p>
        <div className="flex justify-end space-x-4">
          <button
            onClick={logout}
            className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
          >
            Logout
          </button>
          <button
            onClick={extendSession}
            className="px-4 py-2 bg-black text-white border border-gray-600 rounded hover:bg-gray-800"
          >
            Extend Session
          </button>
        </div>
      </div>
    </div>
  );
};

export default SessionTimeout;
