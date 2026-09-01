import { classifyEwayFiles as classifyEwayFilesLocal } from '../utils/excel/ewayDetector';
import { mergeEwayFiles as mergeEwayFilesLocal } from '../utils/excel/ewayMerger';

export async function classifyEwayFiles(files, {
  dealerGstin = '',
  expectedDirection = null,
} = {}) {
  return classifyEwayFilesLocal(files, {
    dealerGstin,
    expectedDirection,
  });
}

export async function validateEwayFiles(files, expectedDirection, dealerGstin = '') {
  return classifyEwayFilesLocal(files, {
    dealerGstin,
    expectedDirection,
  });
}

export async function mergeEwayWorkflow(files, direction, ignoreMissing = false, dealerGstin = '') {
  return mergeEwayFilesLocal(files, direction, {
    ignoreMissing,
    dealerGstin,
  });
}
