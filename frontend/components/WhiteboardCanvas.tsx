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
    Link
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
    className?: string
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

export default function WhiteboardCanvas({ onSave, className = '' }: WhiteboardCanvasProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null)
    const [blocks, setBlocks] = useState<SystemBlock[]>([])
    const [connections, setConnections] = useState<Connection[]>([])
    const [selectedBlock, setSelectedBlock] = useState<string | null>(null)
    const [isConnecting, setIsConnecting] = useState(false)
    const [connectionStart, setConnectionStart] = useState<string | null>(null)
    const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null)
    const containerRef = useRef<HTMLDivElement>(null)

    // Simple undo/redo stacks
    const [history, setHistory] = useState<Array<{ blocks: SystemBlock[]; connections: Connection[] }>>([])
    const [redoStack, setRedoStack] = useState<Array<{ blocks: SystemBlock[]; connections: Connection[] }>>([])

    const snapshot = useCallback(() => {
        // Avoid capturing an empty baseline so first Undo never wipes the canvas
        if (blocks.length === 0 && connections.length === 0) return
        setHistory(prev => [
            ...prev.slice(-49),
            { blocks: JSON.parse(JSON.stringify(blocks)), connections: JSON.parse(JSON.stringify(connections)) }
        ])
        setRedoStack([])
    }, [blocks, connections])
    const [isDragging, setIsDragging] = useState(false)
    const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
    const [selectedTool, setSelectedTool] = useState<'select' | 'connect'>('select')
    const [selectedConnectionId, setSelectedConnectionId] = useState<string | null>(null)

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
            ctx.strokeStyle = selectedBlock === block.id ? '#111827' : blockConfig.borderHex
            ctx.lineWidth = selectedBlock === block.id ? 3 : 1
            ctx.strokeRect(block.x, block.y, block.width, block.height)

            // Label
            ctx.fillStyle = '#ffffff'
            ctx.font = 'bold 12px Arial'
            ctx.textAlign = 'center'
            ctx.fillText(block.label, block.x + block.width / 2, block.y + block.height / 2 + 4)
        })
    }, [blocks, connections, selectedBlock])

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
            setSelectedBlock(null)
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
                    setMousePos(null)
                }
            } else {
                setSelectedBlock(clickedBlock.id)
            }
        } else {
            // Clicking on empty canvas should only change selection state.
            // It must not modify blocks or connections.
            setSelectedBlock(null)
            setSelectedConnectionId(null)
            if (selectedTool === 'connect') {
                setConnectionStart(null)
                setIsConnecting(false)
                setMousePos(null)
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
            setSelectedBlock(clickedBlock.id)
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

        if (!isDragging || !selectedBlock) return
        setBlocks(prev => prev.map(block => (
            block.id === selectedBlock
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
        if (!selectedBlock) return

        // Snapshot this discrete delete action
        snapshot()
        // Remove connections involving this block
        setConnections(prev => prev.filter(conn =>
            conn.from !== selectedBlock && conn.to !== selectedBlock
        ))

        // Remove block
        setBlocks(prev => prev.filter(block => block.id !== selectedBlock))
        setSelectedBlock(null)
    }

    // Clear canvas
    const clearCanvas = () => {
        // Snapshot clear action
        snapshot()
        setBlocks([])
        setConnections([])
        setSelectedBlock(null)
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
        setSelectedBlock(null)
        setConnectionStart(null)
        setIsConnecting(false)
        setMousePos(null)
    }

    const handleRedo = () => {
        const next = redoStack[redoStack.length - 1]
        if (!next) return
        const current = { blocks: JSON.parse(JSON.stringify(blocks)), connections: JSON.parse(JSON.stringify(connections)) }
        setHistory(h => [...h, current])
        setBlocks(next.blocks)
        setConnections(next.connections)
        setRedoStack(r => r.slice(0, -1))
        setSelectedBlock(null)
        setConnectionStart(null)
        setIsConnecting(false)
        setMousePos(null)
    }

    return (
        <div className={`flex flex-col h-full ${className}`}>
            {/* Toolbar */}
            <Card className="mb-4">
                <CardHeader className="pb-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                        <Plus className="w-5 h-5" />
                        System Design Whiteboard
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-wrap gap-2 mb-4">
                        <Button
                            variant={selectedTool === 'select' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setSelectedTool('select')}
                            className="flex items-center gap-2"
                        >
                            <Move className="w-4 h-4" />
                            Select
                        </Button>
                        <Button
                            variant={selectedTool === 'connect' ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => setSelectedTool('connect')}
                            className="flex items-center gap-2"
                        >
                            <Link className="w-4 h-4" />
                            Connect
                        </Button>
                    </div>

                    <div className="flex flex-wrap gap-2 mb-4">
                        {Object.entries(BLOCK_TYPES).map(([type, config]) => {
                            const IconComponent = config.icon
                            return (
                                <Button
                                    key={type}
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleBlockTypeClick(type as SystemBlock['type'])}
                                    className="flex items-center gap-2"
                                >
                                    <IconComponent className="w-4 h-4" />
                                    {config.label}
                                </Button>
                            )
                        })}
                    </div>

                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={clearCanvas}
                            className="flex items-center gap-2"
                        >
                            <Trash2 className="w-4 h-4" />
                            Clear
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={saveCanvas}
                            className="flex items-center gap-2"
                        >
                            <Download className="w-4 h-4" />
                            Save PNG
                        </Button>
                        {selectedBlock && (
                            <Button
                                variant="destructive"
                                size="sm"
                                onClick={deleteSelectedBlock}
                                className="flex items-center gap-2"
                            >
                                <Trash2 className="w-4 h-4" />
                                Delete Block
                            </Button>
                        )}
                    </div>
                </CardContent>
            </Card>

            {/* Canvas */}
            <div ref={containerRef} className="flex-1 bg-white border rounded-lg overflow-hidden">
                <canvas
                    ref={canvasRef}
                    className={`w-full h-full ${selectedTool === 'select' ? 'cursor-move' : 'cursor-crosshair'}`}
                    onClick={handleCanvasClick}
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                />
            </div>

            {/* Status Bar */}
            <div className="mt-2 text-sm text-gray-600 flex items-center justify-between">
                <div>
                    {selectedTool === 'connect' && connectionStart && (
                        <span className="text-blue-600">
                            Click on another block to create connection
                        </span>
                    )}
                    {selectedTool === 'select' && (
                        <span>Click and drag blocks to move them</span>
                    )}
                </div>
                <div className="flex items-center gap-4">
                    <span>Blocks: {blocks.length}</span>
                    <span>Connections: {connections.length}</span>
                    {selectedBlock && (
                        <Badge variant="secondary">
                            Selected: {blocks.find(b => b.id === selectedBlock)?.label}
                        </Badge>
                    )}
                    {selectedConnectionId && (
                        <Badge variant="secondary">Connection selected</Badge>
                    )}
                </div>
            </div>
            {/* Actions */}
            <div className="mt-2 flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={handleUndo} className="flex items-center gap-2">
                    <RotateCcw className="w-4 h-4" /> Undo
                </Button>
                <Button variant="outline" size="sm" onClick={handleRedo} className="flex items-center gap-2">
                    <RotateCw className="w-4 h-4" /> Redo
                </Button>
                {selectedConnectionId && (
                    <div className="flex items-center gap-2 ml-2">
                        <span className="text-sm text-gray-600">Label:</span>
                        <Input
                            value={connections.find(c => c.id === selectedConnectionId)?.label ?? ''}
                            onChange={e => {
                                const newLabel = e.target.value
                                snapshot()
                                setConnections(prev => prev.map(c => c.id === selectedConnectionId ? { ...c, label: newLabel } : c))
                            }}
                            placeholder="e.g., HTTP, gRPC, Kafka"
                            className="h-8 w-56"
                        />
                    </div>
                )}
            </div>
        </div>
    )
}
