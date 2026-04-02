import { useParams, Navigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import * as api from '@/lib/api'
import BoardPage from '@/pages/BoardPage'
import MediaBoardPage from '@/pages/MediaBoardPage'

export default function BoardRouter() {
  const { id } = useParams<{ id: string }>()
  const boardId = Number(id)

  if (!id || isNaN(boardId)) {
    return <Navigate to="/board/1" replace />
  }

  const { data: board, isLoading, error } = useQuery({
    queryKey: ['board', boardId],
    queryFn: () => api.getBoard(boardId),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (error || !board) {
    return <Navigate to="/board/1" replace />
  }

  if (board.board_type === 'media') {
    return <MediaBoardPage boardId={boardId} />
  }

  return <BoardPage />
}
