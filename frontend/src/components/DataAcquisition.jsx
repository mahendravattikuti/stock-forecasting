import React from 'react';
import PipelineControl from './PipelineControl';

/**
 * DataAcquisition Component
 * 
 * Main interface for data acquisition and pipeline execution.
 * Now uses the new PipelineControl component with real API integration.
 * 
 * @component
 * @returns {React.ReactNode} Data acquisition interface
 */
export default function DataAcquisition() {
  return <PipelineControl />;
}
