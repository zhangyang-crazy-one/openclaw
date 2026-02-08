#!/usr/bin/env python3
"""
Accessibility Tree Builder for Browser Automation

Based on Stagehand's hybrid accessibility tree design
"""

import json
from typing import Any, Dict, List, Optional


class AccessibilityTreeBuilder:
    """Build page accessibility tree for AI element positioning."""
    
    JS_SCRIPT = """
    () => {
        const elements = [];
        const seen = new Set();
        
        function extractElement(el, depth) {
            if (depth > 4) return;
            
            const tag = el.tagName.toLowerCase();
            const id = el.id || '';
            const className = el.className;
            const cls = typeof className === 'string' ? className.split(' ')[0] : '';
            
            const selector = id ? '#' + id : tag + '.' + cls;
            const key = selector + depth;
            
            if (seen.has(key) && !id) return;
            seen.add(key);
            
            const role = el.getAttribute('role') || '';
            const name = el.innerText ? el.innerText.trim().substring(0, 100) : 
                         el.getAttribute('name') || el.getAttribute('aria-label') || '';
            const placeholder = el.getAttribute('placeholder') || '';
            const type = el.type || '';
            const value = el.value ? el.value.toString().substring(0, 50) : '';
            
            const interactiveTags = ['a', 'button', 'input', 'select', 'textarea'];
            const isInteractive = interactiveTags.includes(tag) || 
                                   el.onclick || 
                                   (role && role.includes('button'));
            
            const rect = el.getBoundingClientRect();
            const visible = rect.width > 0 && rect.height > 0 && 
                           rect.top >= 0 && rect.left >= 0 &&
                           rect.bottom <= window.innerHeight && rect.right <= window.innerWidth;
            
            if (visible || isInteractive) {
                elements.push({
                    tag: tag,
                    selector: id ? '[id="' + id + '"]' : undefined,
                    role: role,
                    name: name.substring(0, 100),
                    placeholder: placeholder.substring(0, 50),
                    type: type,
                    value: value,
                    interactive: isInteractive
                });
            }
            
            if (depth < 3 && el.children) {
                for (let i = 0; i < el.children.length; i++) {
                    extractElement(el.children[i], depth + 1);
                }
            }
        }
        
        const body = document.body;
        if (body) {
            extractElement(body, 0);
        }
        
        return elements.slice(0, 50);
    }
    """
    
    async def build_tree(self, page) -> str:
        """Build page accessibility tree."""
        try:
            tree = await page.evaluate(self.JS_SCRIPT)
            return self._format_for_llm(tree)
        except Exception as e:
            print("A11y tree error:", e)
            return ""
    
    def _format_for_llm(self, elements: List[Dict]) -> str:
        """Format elements for LLM readability."""
        lines = []
        for i, el in enumerate(elements):
            parts = []
            if el.get('tag'):
                tag = el['tag']
                if el.get('type'):
                    tag += ' type="' + el['type'] + '"'
                if el.get('role'):
                    tag += ' role="' + el['role'] + '"'
                parts.append(tag)
            
            if el.get('name'):
                parts.append(' "' + el['name'][:50] + '"')
            elif el.get('placeholder'):
                parts.append(' placeholder="' + el['placeholder'][:30] + '"')
            
            if el.get('interactive'):
                parts.append(' [interactive]')
            
            lines.append(str(i) + ': ' + ' '.join(parts))
        
        return '\n'.join(lines)
    
    def build_action_prompt(
        self,
        instruction: str,
        dom_elements: str,
        supported_actions: List[str] = None
    ) -> Dict:
        """Build action execution prompt."""
        
        if supported_actions is None:
            supported_actions = [
                "click", "hover", "scroll", "fill", "press", 
                "wait", "goto", "screenshot"
            ]
        
        prompt = """You are helping the user automate the browser.

You will be given:
1. A user instruction about what action to take
2. A list of DOM elements

Return JSON with the element to interact with.

Supported actions: """ + ', '.join(supported_actions) + """

DOM Elements:
""" + dom_elements + """

User Instruction: """ + instruction + """

Respond with JSON:
{
    "element_id": 0,
    "method": "click",
    "arguments": ["left"],
    "reasoning": "why this element"
}

If no match:
{"element_id": -1}"""
        
        return {"role": "user", "content": prompt}
    
    def build_extract_prompt(
        self,
        instruction: str,
        dom_elements: str
    ) -> Dict:
        """Build data extraction prompt."""
        
        prompt = """You are extracting content from a webpage.

You will be given:
1. An extraction instruction
2. DOM elements from the page

Extract ALL information that matches the instruction.

DOM Elements:
""" + dom_elements + """

Instruction: """ + instruction + """

Respond with JSON:
{
    "extracted": "extracted content",
    "source": "element description"
}"""
        
        return {"role": "user", "content": prompt}
    
    def build_observe_prompt(
        self,
        instruction: str,
        dom_elements: str,
        supported_actions: List[str] = None
    ) -> Dict:
        """Build observation prompt."""
        
        if supported_actions is None:
            supported_actions = ["click", "hover", "scroll", "fill"]
        
        prompt = """You are observing elements on the page.

Find elements matching the instruction.

DOM Elements:
""" + dom_elements + """

Instruction: """ + instruction + """

Respond with JSON:
{
    "elements": [matching element indices],
    "description": "page structure"
}"""
        
        return {"role": "user", "content": prompt}
