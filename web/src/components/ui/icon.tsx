/**
 * 通用图标组件
 * 封装 Font Awesome 图标，提供统一的接口
 */

'use client'

import React from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { IconProp, SizeProp } from '@fortawesome/fontawesome-svg-core'
import { cn } from '@/lib/utils'
import { getFAIcon } from '@/lib/fontawesome'

export interface IconProps {
  /**
   * 图标名称（支持 Lucide 风格或 Font Awesome 风格）
   */
  icon: string | IconProp

  /**
   * 图标大小
   */
  size?: SizeProp | number

  /**
   * 是否旋转动画
   */
  spin?: boolean

  /**
   * 是否脉冲动画
   */
  pulse?: boolean

  /**
   * 是否固定宽度
   */
  fixedWidth?: boolean

  /**
   * 自定义类名
   */
  className?: string

  /**
   * 样式
   */
  style?: React.CSSProperties

  /**
   * 标题
   */
  title?: string

  /**
   * ARIA 标签
   */
  'aria-label'?: string

  /**
   * 点击事件处理器
   */
  onClick?: React.MouseEventHandler<SVGSVGElement>
}

/**
 * Icon 组件
 *
 * @example
 * ```tsx
 * <Icon icon="play" className="text-blue-500" />
 * <Icon icon="spinner" spin />
 * <Icon icon={['fas', 'play']} size="2x" />
 * ```
 */
export const Icon: React.FC<IconProps> = ({
  icon,
  size,
  spin = false,
  pulse = false,
  fixedWidth = false,
  className,
  ...props
}) => {
  // 处理图标名称
  let iconProp: IconProp

  if (typeof icon === 'string') {
    // 字符串类型：转换为 Font Awesome 图标名
    const faIconName = getFAIcon(icon)
    iconProp = ['fas', faIconName] as IconProp
  } else {
    // 已经是 IconProp 类型
    iconProp = icon
  }

  // 处理尺寸
  let iconSize: SizeProp | undefined
  if (typeof size === 'number') {
    // 数字尺寸转换为 Tailwind 类
    className = cn(className, `w-${size} h-${size}`)
  } else {
    iconSize = size
  }

  return (
    <FontAwesomeIcon
      icon={iconProp}
      size={iconSize}
      spin={spin}
      pulse={pulse}
      fixedWidth={fixedWidth}
      className={cn('inline-block', className)}
      {...props}
    />
  )
}

/**
 * 常用图标快捷组件
 */
export const Icons = {
  Play: (props: Omit<IconProps, 'icon'>) => <Icon icon="play" {...props} />,
  Pause: (props: Omit<IconProps, 'icon'>) => <Icon icon="pause" {...props} />,
  Upload: (props: Omit<IconProps, 'icon'>) => <Icon icon="upload" {...props} />,
  Download: (props: Omit<IconProps, 'icon'>) => <Icon icon="download" {...props} />,
  Spinner: (props: Omit<IconProps, 'icon'>) => <Icon icon="spinner" spin {...props} />,
  Check: (props: Omit<IconProps, 'icon'>) => <Icon icon="circle-check" {...props} />,
  Close: (props: Omit<IconProps, 'icon'>) => <Icon icon="xmark" {...props} />,
  Refresh: (props: Omit<IconProps, 'icon'>) => <Icon icon="arrows-rotate" {...props} />,
  Video: (props: Omit<IconProps, 'icon'>) => <Icon icon="video" {...props} />,
  Audio: (props: Omit<IconProps, 'icon'>) => <Icon icon="file-audio" {...props} />,
  Language: (props: Omit<IconProps, 'icon'>) => <Icon icon="language" {...props} />,
  Settings: (props: Omit<IconProps, 'icon'>) => <Icon icon="gear" {...props} />,
  Star: (props: Omit<IconProps, 'icon'>) => <Icon icon="star" {...props} />,
  Heart: (props: Omit<IconProps, 'icon'>) => <Icon icon="heart" {...props} />,
  Search: (props: Omit<IconProps, 'icon'>) => <Icon icon="search" {...props} />,
  Filter: (props: Omit<IconProps, 'icon'>) => <Icon icon="filter" {...props} />,
}

export default Icon
