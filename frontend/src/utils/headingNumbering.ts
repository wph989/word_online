/**
 * 前端标题编号生成器
 * 用于在编辑器中实时显示标题编号
 */

export interface HeadingNumberingConfig {
    enabled: boolean;
    style?: string;
}

export class HeadingNumberGenerator {
    private counters: Map<number, number[]> = new Map();
    private style: string;
    private enabled: boolean;

    constructor(config: HeadingNumberingConfig | null) {
        this.enabled = config?.enabled || false;
        this.style = config?.style || 'style2';
    }

    reset() {
        this.counters.clear();
    }

    getNumber(level: number): string {
        if (!this.enabled) {
            return '';
        }

        level = Math.max(1, Math.min(6, level));
        this.updateCounter(level);

        const formats = this.getStyleFormats();
        const format = formats[level] || 'hierarchical';
        
        return this.generateNumber(level, format);
    }

    private updateCounter(level: number) {
        if (level === 1) {
            if (!this.counters.has(1)) {
                this.counters.set(1, [1]);
            } else {
                const current = this.counters.get(1)!;
                this.counters.set(1, [current[0] + 1]);
            }
            // 清除更深层级
            for (let l = 2; l <= 6; l++) {
                this.counters.delete(l);
            }
        } else {
            const parentLevel = level - 1;
            
            if (!this.counters.has(parentLevel)) {
                this.counters.set(parentLevel, Array(parentLevel).fill(1));
            }
            
            if (!this.counters.has(level)) {
                const parentCounters = this.counters.get(parentLevel)!;
                this.counters.set(level, [...parentCounters, 1]);
            } else {
                const current = this.counters.get(level)!;
                const parentCounters = this.counters.get(parentLevel)!;
                
                if (current.length < level || !this.arraysEqual(current.slice(0, parentLevel), parentCounters)) {
                    this.counters.set(level, [...parentCounters, 1]);
                } else {
                    current[current.length - 1]++;
                }
            }
            
            // 清除更深层级
            for (let l = level + 1; l <= 6; l++) {
                this.counters.delete(l);
            }
        }
    }

    private arraysEqual(a: number[], b: number[]): boolean {
        return a.length === b.length && a.every((val, idx) => val === b[idx]);
    }

    private getStyleFormats(): Record<number, string> {
        const presetStyles: Record<string, Record<number, string>> = {
            style1: {
                1: 'chinese',
                2: 'hierarchical',
                3: 'parenthesis',
                4: 'hierarchical',
                5: 'parenthesis',
                6: 'circled'
            },
            style2: {
                1: 'number',
                2: 'hierarchical',
                3: 'hierarchical',
                4: 'hierarchical',
                5: 'hierarchical',
                6: 'hierarchical'
            },
            style3: {
                1: 'number_dot',
                2: 'hierarchical',
                3: 'hierarchical',
                4: 'hierarchical',
                5: 'hierarchical',
                6: 'hierarchical'
            },
            style4: {
                1: 'chapter',
                2: 'hierarchical',
                3: 'hierarchical',
                4: 'hierarchical',
                5: 'hierarchical',
                6: 'hierarchical'
            }
        };

        return presetStyles[this.style] || presetStyles.style2;
    }

    private generateNumber(level: number, format: string): string {
        const counters = this.counters.get(level) || [1];
        const currentNum = counters[counters.length - 1];

        switch (format) {
            case 'chinese':
                return this.toChineseNumber(currentNum) + '、';
            
            case 'number':
                return `${currentNum}、`;
            
            case 'number_dot':
                return `${currentNum}. `;
            
            case 'hierarchical':
                return counters.join('.') + ' ';
            
            case 'parenthesis':
                return `(${currentNum}) `;
            
            case 'circled':
                if (currentNum <= 10) {
                    const circled = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩'];
                    return circled[currentNum - 1] + ' ';
                }
                return `(${currentNum}) `;
            
            case 'chapter':
                if (currentNum <= 10) {
                    return `第${this.toChineseNumber(currentNum)}章 `;
                }
                return `第${currentNum}章 `;
            
            case 'none':
                return '';
            
            default:
                return counters.join('.') + ' ';
        }
    }

    private toChineseNumber(num: number): string {
        const chineseNumbers = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
        
        if (num <= 0) return '零';
        if (num <= 10) return chineseNumbers[num];
        if (num < 20) return '十' + chineseNumbers[num - 10];
        
        const tens = Math.floor(num / 10);
        const ones = num % 10;
        let result = chineseNumbers[tens] + '十';
        if (ones > 0) result += chineseNumbers[ones];
        return result;
    }
}
