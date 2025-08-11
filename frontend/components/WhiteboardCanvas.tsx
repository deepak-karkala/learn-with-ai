'use client'

import React, { useRef, useState, useCallback, useEffect } from 'react'
import { Button } from './ui/button'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { Input } from './ui/input'
import { Separator } from './ui/separator'
import {
    Database,
    Server,
    Globe,
    Shield,
    Cpu,
    HardDrive,
    Network,
    Zap,
    Trash2,
    Download,
    RotateCcw,
    RotateCw,
    Plus,
    Move,
    Link,
    Target,
    MousePointer,
    Undo,
    Redo,
    Loader2
} from 'lucide-react'

export interface SystemBlock {
    id: string
    type: 'load-balancer' | 'web-server' | 'database' | 'redis' | 'api-gateway' | 'cdn' | 'queue' | 'cache' | 'monitoring' | 'logging'
    x: number
    y: number
    width: number
    height: number
    label: string
    connections: string[] // IDs of connected blocks
}

export interface Connection {
    id: string
    from: string
    to: string
    label: string
}

interface WhiteboardCanvasProps {
    onSave?: (pngData: string) => void
    onAnalyze?: (pngData: string) => void
    isAnalyzing?: boolean
}

const BLOCK_TYPES = {
    'load-balancer': {
        label: 'Load Balancer',
        icon: Globe,
        fillColor: '#3b82f6',
        borderHex: '#2563eb',
        width: 120,
        height: 80
    },
    'web-server': {
        label: 'Web Server',
        icon: Server,
        fillColor: '#22c55e',
        borderHex: '#16a34a',
        width: 100,
        height: 60
    },
    'database': {
        label: 'Database',
        icon: Database,
        fillColor: '#a855f7',
        borderHex: '#9333ea',
        width: 100,
        height: 60
    },
    'redis': {
        label: 'Redis Cache',
        icon: Zap,
        fillColor: '#ef4444',
        borderHex: '#dc2626',
        width: 100,
        height: 60
    },
    'api-gateway': {
        label: 'API Gateway',
        icon: Shield,
        fillColor: '#6366f1',
        borderHex: '#4f46e5',
        width: 120,
        height: 80
    },
    'cdn': {
        label: 'CDN',
        icon: Network,
        fillColor: '#f97316',
        borderHex: '#ea580c',
        width: 100,
        height: 60
    },
    'queue': {
        label: 'Message Queue',
        icon: HardDrive,
        fillColor: '#14b8a6',
        borderHex: '#0d9488',
        width: 120,
        height: 60
    },
    'cache': {
        label: 'Cache',
        icon: Cpu,
        fillColor: '#ec4899',
        borderHex: '#db2777',
        width: 100,
        height: 60
    },
    'monitoring': {
        label: 'Monitoring',
        icon: Shield,
        fillColor: '#eab308',
        borderHex: '#ca8a04',
        width: 100,
        height: 60
    },
    'logging': {
        label: 'Logging',
        icon: HardDrive,
        fillColor: '#6b7280',
        borderHex: '#4b5563',
        width: 100,
        height: 60
    }
}

export function WhiteboardCanvas({ onSave, onAnalyze, isAnalyzing }: WhiteboardCanvasProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const [selectedTool, setSelectedTool] = useState<'select' | 'connect'>('select')
    const [blocks, setBlocks] = useState<SystemBlock[]>([])
    const [connections, setConnections] = useState<Connection[]>([])
    const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null)
    const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null)
    const [isConnecting, setIsConnecting] = useState(false)
    const [connectionStart, setConnectionStart] = useState<string | null>(null)
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
    const [isDragging, setIsDragging] = useState(false)
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
    const [editingConnectionId, setEditingConnectionId] = useState<string | null>(null)
    const [editingLabel, setEditingLabel] = useState('')
    const [history, setHistory] = useState<Array<{ blocks: SystemBlock[], connections: Connection[] }>>([])
    const [redoStack, setRedoStack] = useState<Array<{ blocks: SystemBlock[], connections: Connection[] }>>([])

    // Simple undo/redo stacks
    const snapshot = useCallback(() => {
        // Avoid capturing an empty baseline so first Undo never wipes the canvas
        if (blocks.length === 0 && connections.length === 0) return
        setHistory(prev => [
            ...prev.slice(-49),
            { blocks: JSON.parse(JSON.stringify(blocks)), connections: JSON.parse(JSON.stringify(connections)) }
        ])
        setRedoStack([])
    }, [blocks, connections])

    // Initialize canvas
    // Keep a ref to the latest draw function so resize callbacks can repaint immediately
    const drawRef = useRef<() => void>(() => { })
    useEffect(() => {
        // Initialize to a no-op; will be replaced after drawCanvas is defined
        drawRef.current = () => { }
    }, [])

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return

        const setSizeAndRedraw = () => {
            const parent = canvas.parentElement
            const width = parent?.clientWidth || 1000
            const height = parent?.clientHeight || 600
            const sizeChanged = canvas.width !== width || canvas.height !== height
            if (sizeChanged) {
                canvas.width = width
                canvas.height = height
                // Redraw immediately after a size change, since resizing clears the canvas
                requestAnimationFrame(() => drawRef.current())
            }
        }

        setSizeAndRedraw()
        const ro = new ResizeObserver(() => setSizeAndRedraw())
        ro.observe(canvas.parentElement || canvas)
        return () => ro.disconnect()
    }, [])

    // Draw function
    const drawCanvas = useCallback(() => {
        const canvas = canvasRef.current
        if (!canvas) return

        const ctx = canvas.getContext('2d')
        if (!ctx) return

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height)

        // Draw connections first (behind blocks)
        connections.forEach(connection => {
            const fromBlock = blocks.find(b => b.id === connection.from)
            const toBlock = blocks.find(b => b.id === connection.to)

            if (fromBlock && toBlock) {
                const fromX = fromBlock.x + fromBlock.width / 2
                const fromY = fromBlock.y + fromBlock.height / 2
                const toX = toBlock.x + toBlock.width / 2
                const toY = toBlock.y + toBlock.height / 2

                // Draw connection line
                ctx.beginPath()
                ctx.moveTo(fromX, fromY)
                ctx.lineTo(toX, toY)
                ctx.strokeStyle = '#6b7280'
                ctx.lineWidth = 2
                ctx.stroke()

                // Draw arrow
                const angle = Math.atan2(toY - fromY, toX - fromX)
                const arrowLength = 10
                const arrowAngle = Math.PI / 6

                ctx.beginPath()
                ctx.moveTo(toX, toY)
                ctx.lineTo(
                    toX - arrowLength * Math.cos(angle - arrowAngle),
                    toY - arrowLength * Math.sin(angle - arrowAngle)
                )
                ctx.moveTo(toX, toY)
                ctx.lineTo(
                    toX - arrowLength * Math.cos(angle + arrowAngle),
                    toY - arrowLength * Math.sin(angle + arrowAngle)
                )
                ctx.stroke()

                // Draw connection label
                const midX = (fromX + toX) / 2
                const midY = (fromY + toY) / 2
                ctx.fillStyle = '#374151'
                ctx.font = selectedConnectionId === connection.id ? 'bold 12px Arial' : '12px Arial'
                ctx.textAlign = 'center'
                ctx.fillText((connection.label || '').toString(), midX, midY - 5)
            }
        })

        // Draw preview connection if connecting
        if (isConnecting && connectionStart && mousePos) {
            const startBlock = blocks.find(b => b.id === connectionStart)
            if (startBlock) {
                const fromX = startBlock.x + startBlock.width / 2
                const fromY = startBlock.y + startBlock.height / 2
                const toX = mousePos.x
                const toY = mousePos.y

                ctx.beginPath()
                ctx.setLineDash([6, 6])
                ctx.moveTo(fromX, fromY)
                ctx.lineTo(toX, toY)
                ctx.strokeStyle = '#2563eb'
                ctx.lineWidth = 2
                ctx.stroke()
                ctx.setLineDash([])
            }
        }

        // Draw blocks (uniform rectangle style for all types)
        blocks.forEach(block => {
            const blockConfig = BLOCK_TYPES[block.type]
            if (!blockConfig) return

            // Background
            ctx.fillStyle = blockConfig.fillColor
            ctx.fillRect(block.x, block.y, block.width, block.height)

            // Border
            ctx.strokeStyle = selectedBlockId === block.id ? '#111827' : blockConfig.borderHex
            ctx.lineWidth = selectedBlockId === block.id ? 3 : 1
            ctx.strokeRect(block.x, block.y, block.width, block.height)

            // Label
            ctx.fillStyle = '#ffffff'
            ctx.font = 'bold 12px Arial'
            ctx.textAlign = 'center'
            ctx.fillText(block.label, block.x + block.width / 2, block.y + block.height / 2 + 4)
        })
    }, [blocks, connections, selectedBlockId])

    // Redraw canvas when blocks or connections change, and avoid flicker by batching in rAF
    useEffect(() => {
        let raf: number | null = null
        const paint = () => {
            drawCanvas()
            // keep drawRef in sync with latest drawCanvas so external callbacks are safe
            drawRef.current = drawCanvas
            raf = null
        }
        raf = requestAnimationFrame(paint)
        return () => {
            if (raf) cancelAnimationFrame(raf)
        }
    }, [drawCanvas])

    // Add new block
    const addBlock = (type: SystemBlock['type'], x: number, y: number) => {
        const blockConfig = BLOCK_TYPES[type]
        if (!blockConfig) return

        const newBlock: SystemBlock = {
            id: `block-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            type,
            x: x - blockConfig.width / 2,
            y: y - blockConfig.height / 2,
            width: blockConfig.width,
            height: blockConfig.height,
            label: blockConfig.label,
            connections: []
        }

        // Snapshot this discrete add action
        snapshot()
        setBlocks(prev => [...prev, newBlock])
    }

    // Utility: distance from point to line segment
    const pointToSegmentDistance = (px: number, py: number, x1: number, y1: number, x2: number, y2: number): number => {
        const dx = x2 - x1
        const dy = y2 - y1
        if (dx === 0 && dy === 0) return Math.hypot(px - x1, py - y1)
        const t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        const cx = x1 + t * dx
        const cy = y1 + t * dy
        return Math.hypot(px - cx, py - cy)
    }

    // Handle canvas click
    const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current
        if (!canvas) return

        const rect = canvas.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top

        // Check if clicking near a connection line
        const hitThreshold = 8
        let hitConnectionId: string | null = null
        for (const conn of connections) {
            const fromBlock = blocks.find(b => b.id === conn.from)
            const toBlock = blocks.find(b => b.id === conn.to)
            if (!fromBlock || !toBlock) continue
            const fromX = fromBlock.x + fromBlock.width / 2
            const fromY = fromBlock.y + fromBlock.height / 2
            const toX = toBlock.x + toBlock.width / 2
            const toY = toBlock.y + toBlock.height / 2
            const dist = pointToSegmentDistance(x, y, fromX, fromY, toX, toY)
            if (dist <= hitThreshold) {
                hitConnectionId = conn.id
                break
            }
        }

        if (hitConnectionId) {
            setSelectedConnectionId(hitConnectionId)
            setSelectedBlockId(null)
            return
        } else {
            setSelectedConnectionId(null)
        }

        // Check if clicking on a block
        const clickedBlock = blocks.find(block =>
            x >= block.x && x <= block.x + block.width &&
            y >= block.y && y <= block.y + block.height
        )

        if (clickedBlock) {
            if (selectedTool === 'connect') {
                if (!connectionStart) {
                    setConnectionStart(clickedBlock.id)
                    setIsConnecting(true)
                } else if (connectionStart !== clickedBlock.id) {
                    // Create connection
                    // Snapshot this discrete connect action
                    snapshot()
                    const newConnection: Connection = {
                        id: `conn-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
                        from: connectionStart,
                        to: clickedBlock.id,
                        label: 'text'
                    }
                    setConnections(prev => [...prev, newConnection])
                    setConnectionStart(null)
                    setIsConnecting(false)
                    setMousePos({ x: 0, y: 0 }) // Reset mousePos after connection
                }
            } else {
                setSelectedBlockId(clickedBlock.id)
            }
        } else {
            // Clicking on empty canvas should only change selection state.
            // It must not modify blocks or connections.
            setSelectedBlockId(null)
            setSelectedConnectionId(null)
            if (selectedTool === 'connect') {
                setConnectionStart(null)
                setIsConnecting(false)
                setMousePos({ x: 0, y: 0 }) // Reset mousePos after connection attempt
            }
        }
    }

    // Handle mouse down for dragging
    const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current
        if (!canvas) return

        const rect = canvas.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top

        const clickedBlock = blocks.find(block =>
            x >= block.x && x <= block.x + block.width &&
            y >= block.y && y <= block.y + block.height
        )

        if (selectedTool === 'connect') {
            if (clickedBlock && !connectionStart) {
                setConnectionStart(clickedBlock.id)
                setIsConnecting(true)
            }
            return
        }

        if (clickedBlock && selectedTool === 'select') {
            setIsDragging(true)
            setDragOffset({
                x: x - clickedBlock.x,
                y: y - clickedBlock.y
            })
            setSelectedBlockId(clickedBlock.id)
        }
    }

    // Handle mouse move for dragging
    const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
        const canvas = canvasRef.current
        if (!canvas) return

        const rect = canvas.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top

        if (selectedTool === 'connect') {
            if (connectionStart) {
                setMousePos({ x, y })
            }
            return
        }

        if (!isDragging || !selectedBlockId) return
        setBlocks(prev => prev.map(block => (
            block.id === selectedBlockId
                ? { ...block, x: x - dragOffset.x, y: y - dragOffset.y }
                : block
        )))
    }

    // Handle mouse up
    const handleMouseUp = () => {
        if (isDragging) {
            // Record a snapshot for the completed drag action
            snapshot()
        }
        setIsDragging(false)
    }

    // Delete selected block
    const deleteSelectedBlock = () => {
        if (!selectedBlockId) return

        // Snapshot this discrete delete action
        snapshot()
        // Remove connections involving this block
        setConnections(prev => prev.filter(conn =>
            conn.from !== selectedBlockId && conn.to !== selectedBlockId
        ))

        // Remove block
        setBlocks(prev => prev.filter(block => block.id !== selectedBlockId))
        setSelectedBlockId(null)
    }

    // Clear canvas
    const clearCanvas = () => {
        // Snapshot clear action
        snapshot()
        setBlocks([])
        setConnections([])
        setSelectedBlockId(null)
        setConnectionStart(null)
        setIsConnecting(false)
    }

    // Save canvas as PNG
    const saveCanvas = () => {
        const canvas = canvasRef.current
        if (!canvas) return

        try {
            const pngData = canvas.toDataURL('image/png')
            onSave?.(pngData)
        } catch (error) {
            console.error('Failed to save canvas:', error)
        }
    }

    // Handle block type selection
    const handleBlockTypeClick = (type: SystemBlock['type']) => {
        setSelectedTool('select')
        // Add block at center of canvas
        const canvas = canvasRef.current
        if (canvas) {
            const x = canvas.width / 2
            const y = canvas.height / 2
            addBlock(type, x, y)
        }
    }

    const handleUndo = () => {
        const prev = history[history.length - 1]
        if (!prev) return
        const current = { blocks: JSON.parse(JSON.stringify(blocks)), connections: JSON.parse(JSON.stringify(connections)) }
        setRedoStack(r => [...r, current])
        setBlocks(prev.blocks)
        setConnections(prev.connections)
        setHistory(h => h.slice(0, -1))
        setSelectedBlockId(null)
        setConnectionStart(null)
        setIsConnecting(false)
        setMousePos({ x: 0, y: 0 })
    }

    const handleRedo = () => {
        const next = redoStack[redoStack.length - 1]
        if (!next) return
        const current = { blocks: JSON.parse(JSON.stringify(blocks)), connections: JSON.parse(JSON.stringify(connections)) }
        setHistory(h => [...h, current])
        setBlocks(next.blocks)
        setConnections(next.connections)
        setRedoStack(r => r.slice(0, -1))
        setSelectedBlockId(null)
        setConnectionStart(null)
        setIsConnecting(false)
        setMousePos({ x: 0, y: 0 })
    }

    const handleAnalyzeWhiteboard = () => {
        if (!onAnalyze) return

        try {
            const canvas = canvasRef.current
            if (!canvas) return

            const pngData = canvas.toDataURL('image/png')
            onAnalyze(pngData)
        } catch (error) {
            console.error('Failed to analyze whiteboard:', error)
        }
    }

    const handleConnectionLabelEdit = () => {
        if (!editingConnectionId || !editingLabel.trim()) return

        setConnections(prev => prev.map(conn =>
            conn.id === editingConnectionId
                ? { ...conn, label: editingLabel.trim() }
                : conn
        ))

        setEditingConnectionId(null)
        setEditingLabel('')
    }

    const handleCanvasMouseLeave = () => {
        handleMouseUp()
    }

    return (
        <div className="h-full flex flex-col bg-white rounded-lg border border-gray-200">
            {/* Main Action Buttons - Top Priority */}
            <div className="p-4 border-b border-gray-200 bg-blue-50 flex justify-center items-center gap-4">
                <Button
                    variant="default"
                    size="default"
                    onClick={saveCanvas}
                    disabled={blocks.length === 0}
                    className="h-12 px-6 bg-green-600 hover:bg-green-700 text-white font-semibold"
                >
                    <Download className="h-5 w-5 mr-2" />
                    Save PNG
                </Button>
                <Button
                    variant="default"
                    size="default"
                    onClick={handleAnalyzeWhiteboard}
                    disabled={isAnalyzing || blocks.length === 0}
                    className="h-12 px-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold"
                >
                    {isAnalyzing ? (
                        <>
                            <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                            Analyzing...
                        </>
                    ) : (
                        <>
                            <Target className="h-5 w-5 mr-2" />
                            Analyze Design
                        </>
                    )}
                </Button>
            </div>

            {/* Secondary Toolbar */}
            <div className="p-3 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <Button
                        variant={selectedTool === 'select' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setSelectedTool('select')}
                        className="h-8 px-3"
                    >
                        <MousePointer className="h-4 w-4 mr-1" />
                        Select
                    </Button>
                    <Button
                        variant={selectedTool === 'connect' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setSelectedTool('connect')}
                        className="h-8 px-3"
                    >
                        <Link className="h-4 w-4 mr-1" />
                        Connect
                    </Button>
                </div>

                <div className="flex items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleUndo}
                        disabled={history.length === 0}
                        className="h-8 px-3"
                    >
                        <Undo className="h-4 w-4 mr-1" />
                        Undo
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRedo}
                        disabled={redoStack.length === 0}
                        className="h-8 px-3"
                    >
                        <Redo className="h-4 w-4 mr-1" />
                        Redo
                    </Button>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={clearCanvas}
                        className="h-8 px-3"
                    >
                        <Trash2 className="h-4 w-4 mr-1" />
                        Clear
                    </Button>
                </div>

                <div className="flex items-center gap-4">
                    <div className="text-sm text-gray-600 font-medium">
                        {blocks.length} blocks, {connections.length} connections
                    </div>
                    <div className="text-sm text-blue-600 font-medium">
                        Tool: {selectedTool === 'select' ? 'Select' : 'Connect'}
                    </div>
                </div>
            </div>

            {/* Block Type Buttons */}
            <div className="p-3 border-b border-gray-200 bg-gray-50">
                <div className="flex flex-wrap gap-2">
                    {Object.entries(BLOCK_TYPES).map(([type, config]) => {
                        const IconComponent = config.icon
                        return (
                            <Button
                                key={type}
                                variant="outline"
                                size="sm"
                                onClick={() => handleBlockTypeClick(type as SystemBlock['type'])}
                                className="h-8 px-3 text-xs"
                            >
                                <IconComponent className="h-4 w-4 mr-1" />
                                {config.label}
                            </Button>
                        )
                    })}
                </div>
            </div>

            {/* Canvas Container */}
            <div className="flex-1 relative overflow-hidden">
                <canvas
                    ref={canvasRef}
                    className="w-full h-full border border-gray-300 cursor-crosshair"
                    onClick={handleCanvasClick}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                />

                {/* Connection Preview */}
                {isConnecting && connectionStart && (
                    <svg
                        className="absolute inset-0 pointer-events-none"
                        style={{ width: '100%', height: '100%' }}
                    >
                        <line
                            x1={blocks.find(b => b.id === connectionStart)?.x || 0}
                            y1={blocks.find(b => b.id === connectionStart)?.y || 0}
                            x2={mousePos.x}
                            y2={mousePos.y}
                            stroke="blue"
                            strokeWidth="2"
                            strokeDasharray="5,5"
                        />
                    </svg>
                )}

                {/* Connection Label Editor */}
                {editingConnectionId && (
                    <div
                        className="absolute z-10"
                        style={{
                            left: mousePos.x + 10,
                            top: mousePos.y - 20
                        }}
                    >
                        <Input
                            value={editingLabel}
                            onChange={(e) => setEditingLabel(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                    handleConnectionLabelEdit()
                                } else if (e.key === 'Escape') {
                                    setEditingConnectionId(null)
                                    setEditingLabel('')
                                }
                            }}
                            onBlur={handleConnectionLabelEdit}
                            className="w-24 h-8 text-xs"
                            autoFocus
                        />
                    </div>
                )}
            </div>

            {/* Status Bar */}
            <div className="p-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-600">
                <div className="flex items-center justify-between">
                    <span>
                        {blocks.length} blocks, {connections.length} connections
                    </span>
                    <span>
                        Tool: {selectedTool === 'select' ? 'Select' : 'Connect'}
                    </span>
                </div>
            </div>
        </div>
    )
}
