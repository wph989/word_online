/**
 * 表格单元格多选功能 Hook
 * 实现类似 Excel 的表格单元格框选功能
 */

import { useEffect, useRef, useCallback } from 'react';
import { IDomEditor } from '@wangeditor-next/editor';

interface CellPosition {
    row: number;
    col: number;
    cell: HTMLTableCellElement;
}

/**
 * 表格多选 Hook
 * 支持通过鼠标拖拽选择多个单元格
 */
export function useTableMultiSelect(editor: IDomEditor | null) {
    const isSelectingRef = useRef(false);
    const startCellRef = useRef<CellPosition | null>(null);
    const selectedCellsRef = useRef<Set<HTMLTableCellElement>>(new Set());

    // 获取单元格位置
    const getCellPosition = useCallback((cell: HTMLTableCellElement): CellPosition | null => {
        const row = cell.closest('tr');
        if (!row) return null;

        const table = row.closest('table');
        if (!table) return null;

        const rows = Array.from(table.querySelectorAll('tr'));
        const rowIndex = rows.indexOf(row);

        const cells = Array.from(row.querySelectorAll('th, td'));
        const colIndex = cells.indexOf(cell);

        if (rowIndex === -1 || colIndex === -1) return null;

        return { row: rowIndex, col: colIndex, cell };
    }, []);

    // 清除所有选中状态
    const clearSelection = useCallback(() => {
        selectedCellsRef.current.forEach(cell => {
            cell.classList.remove('cell-selected');
        });
        selectedCellsRef.current.clear();
    }, []);

    // 选中指定范围内的单元格
    const selectRange = useCallback((start: CellPosition, end: CellPosition, table: HTMLTableElement) => {
        const minRow = Math.min(start.row, end.row);
        const maxRow = Math.max(start.row, end.row);
        const minCol = Math.min(start.col, end.col);
        const maxCol = Math.max(start.col, end.col);

        // 清除之前的选中
        clearSelection();

        const rows = table.querySelectorAll('tr');
        for (let r = minRow; r <= maxRow; r++) {
            const row = rows[r];
            if (!row) continue;

            const cells = row.querySelectorAll('th, td');
            for (let c = minCol; c <= maxCol; c++) {
                const cell = cells[c] as HTMLTableCellElement;
                if (cell) {
                    cell.classList.add('cell-selected');
                    selectedCellsRef.current.add(cell);
                }
            }
        }
    }, [clearSelection]);

    // 获取选中的单元格
    const getSelectedCells = useCallback((): HTMLTableCellElement[] => {
        return Array.from(selectedCellsRef.current);
    }, []);

    useEffect(() => {
        if (!editor) return;

        const editorEl = document.querySelector('[data-slate-editor]');
        if (!editorEl) return;

        const handleMouseDown = (e: Event) => {
            const event = e as MouseEvent;
            const target = event.target as HTMLElement;
            const cell = target.closest('td, th') as HTMLTableCellElement | null;

            if (!cell) {
                // 点击非单元格区域，清除选中
                clearSelection();
                return;
            }

            // 检查是否按住 Ctrl/Cmd 键
            const isMultiSelect = event.ctrlKey || event.metaKey;

            if (!isMultiSelect) {
                // 没有按住 Ctrl，开始新的选择
                clearSelection();
            }

            const position = getCellPosition(cell);
            if (!position) return;

            isSelectingRef.current = true;
            startCellRef.current = position;

            // 选中起始单元格
            cell.classList.add('cell-selected');
            selectedCellsRef.current.add(cell);
        };

        const handleMouseMove = (e: Event) => {
            if (!isSelectingRef.current || !startCellRef.current) return;

            const event = e as MouseEvent;

            // 阻止默认的文本选择，避免干扰框选
            event.preventDefault();

            // 使用 elementFromPoint 来获取鼠标位置下的元素
            // 这样可以更准确地处理纵向拖动
            const elementAtPoint = document.elementFromPoint(event.clientX, event.clientY);
            if (!elementAtPoint) return;

            const cell = elementAtPoint.closest('td, th') as HTMLTableCellElement | null;

            if (!cell) return;

            const position = getCellPosition(cell);
            if (!position) return;

            const table = cell.closest('table');
            if (!table) return;

            // 确保在同一个表格内
            const startTable = startCellRef.current.cell.closest('table');
            if (table !== startTable) return;

            // 选中从起始单元格到当前单元格的矩形区域
            selectRange(startCellRef.current, position, table);
        };

        const handleMouseUp = () => {
            isSelectingRef.current = false;
        };

        // 添加事件监听
        editorEl.addEventListener('mousedown', handleMouseDown);
        editorEl.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);

        return () => {
            editorEl.removeEventListener('mousedown', handleMouseDown);
            editorEl.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
        };
    }, [editor, clearSelection, getCellPosition, selectRange]);

    return {
        getSelectedCells,
        clearSelection
    };
}
