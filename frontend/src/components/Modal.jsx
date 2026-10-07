import React, { useEffect, useRef } from 'react';

// Native modal supplies focus containment, Escape dismissal, and focus restoration.
export default function Modal({ children, labelledBy, onClose }) {
  const dialog = useRef(null);
  useEffect(() => {
    const element = dialog.current;
    const previousFocus = document.activeElement;
    element.showModal();
    return () => {
      element.close();
      if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus();
    };
  }, []);
  return <dialog ref={dialog} className="policy-dialog" aria-labelledby={labelledBy}
    onCancel={(event) => { event.preventDefault(); onClose(); }}>{children}</dialog>;
}
