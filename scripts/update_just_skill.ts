#!/usr/bin/env bun

import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkStringify from 'remark-stringify';
import remarkGfm from 'remark-gfm';
import fs from 'node:fs';
import path from 'node:path';

const README_URL = 'https://raw.githubusercontent.com/casey/just/refs/heads/master/README.md';
const SKILL_FILE = path.join(import.meta.dir, '..', 'skills', 'justfile', 'SKILL.md');

// Sections to explicitly exclude
const EXCLUDE_SECTIONS = [
  'installation',
  'backwards compatibility',
  'editor support',
  'changelog',
  'miscellanea',
  'contributing',
  'frequently asked questions',
  'further ramblings',
  'packages',
];

// Sections to explicitly include
const INCLUDE_SECTIONS = [
  'quick start',
  'examples',
  'features',
  'the default recipe',
];

function filterSections() {
  return (tree) => {
    const newChildren = [];
    let keeping = true;

    for (const node of tree.children) {
      if (node.type === 'heading') {
        const text = node.children.map(c => c.value).join('').toLowerCase().trim();
        
        if (EXCLUDE_SECTIONS.some(s => text === s || text.startsWith(s + ' '))) {
          keeping = false;
        } else if (INCLUDE_SECTIONS.some(s => text === s || text.startsWith(s + ' '))) {
          keeping = true;
        }
      }

      if (keeping && node.type === 'html') {
        if (node.value.includes('Table of Contents') || 
            (node.value.includes('align=center') && node.value.includes('img.shields.io'))) {
          continue;
        }
      }

      if (keeping) {
        newChildren.push(node);
      }
    }
    tree.children = newChildren;
  };
}

async function main() {
  console.log('Fetching README...');
  const response = await fetch(README_URL);
  if (!response.ok) throw new Error(`Failed to fetch: ${response.statusText}`);
  const markdown = await response.text();

  console.log('Processing Markdown...');
  const processor = unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(filterSections)
    .use(remarkStringify);

  const processed = await processor.process(markdown);
  const newContent = processed.toString();

  console.log('Reading SKILL.md...');
  let skillContent = fs.readFileSync(SKILL_FILE, 'utf-8');

  const MARKER = 'It fully documents the Justfile syntax and system.\n\n---';
  const markerIndex = skillContent.indexOf(MARKER);

  let header;
  if (markerIndex !== -1) {
    header = skillContent.substring(0, markerIndex + MARKER.length);
  } else {
    console.warn('Marker not found! Appending to end.');
    header = skillContent;
    if (!header.trim().endsWith('---')) {
        header += '\n\n---';
    }
  }

  const finalContent = header + '\n\n' + newContent;

  console.log('Writing to SKILL.md...');
  fs.writeFileSync(SKILL_FILE, finalContent);
  console.log('Done.');
}

main().catch(console.error);
