'use client';
import React from 'react';

function subscribe(onStoreChange: () => void) {
    window.addEventListener('scroll', onStoreChange, { passive: true });
    return () => window.removeEventListener('scroll', onStoreChange);
}

export function useScroll(threshold: number) {
    return React.useSyncExternalStore(
        subscribe,
        () => window.scrollY > threshold,
        () => false,
    );
}
