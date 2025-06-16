import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, BookOpen, BarChart2, Users, GitBranch } from 'lucide-react';
import { NavItem } from '../../types';

const navItems: NavItem[] = [
	{
		name: 'Dashboard',
		path: '/',
		icon: <LayoutDashboard className="w-5 h-5" />,
	},
	{
		name: 'Projects',
		path: '/projects',
		icon: <Users className="w-5 h-5" />,
	},
	{
		name: 'Repos',
		path: '/repos',
		icon: <GitBranch className="w-5 h-5" />,
	},
	{
		name: 'Pipelines',
		path: '/pipelines',
		icon: <BarChart2 className="w-5 h-5" />,
	},
	{
		name: 'Releases',
		path: '/releases',
		icon: <BookOpen className="w-5 h-5" />,
	},
];

const Sidebar: React.FC = () => {
	const [collapsed, setCollapsed] = React.useState(false);

	return (
		<aside
			className={`bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-all duration-300 ease-in-out ${
				collapsed ? 'w-16' : 'w-64'
			} flex flex-col h-full`}
		>
			<div className="flex items-center justify-center h-16 border-b border-gray-200 dark:border-gray-800">
				<div className="flex items-center justify-center w-full h-full">
					<img
						src="/devops-logo.png"
						alt="Azure DevOps Logo"
						className="h-12 w-auto object-contain mx-auto"
						style={{ maxWidth: '80%', display: 'block' }}
					/>
				</div>
			</div>
			<nav className="flex-1 pt-4 pb-2 overflow-y-auto">
				<ul className="space-y-1 px-2">
					{navItems.map((item) => (
						<li key={item.path}>
							<NavLink
								to={item.path}
								className={({ isActive }) =>
									`flex items-center px-3 py-2 rounded-md transition-colors group ${
										item.name === 'Projects'
											? isActive
												? 'bg-gradient-to-r from-primary-100 to-primary-50 dark:from-gray-800 dark:to-gray-900 text-primary-700 dark:text-primary-300 shadow-md border border-primary-200 dark:border-primary-800'
												: 'hover:bg-primary-50 dark:hover:bg-gray-800 text-primary-700 dark:text-primary-300 border border-transparent'
										: isActive
											? 'bg-primary-50 dark:bg-gray-800 text-primary-700 dark:text-primary-300'
											: 'text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'
									} ${collapsed ? 'justify-center' : 'justify-start'}`
							}
						>
							<span className={item.name === 'Projects' ? 'relative' : ''}>
								{item.icon && React.cloneElement(item.icon, {
									className: `w-5 h-5 ${item.name === 'Projects' ? 'text-primary-500 group-hover:text-primary-700 transition' : ''}`
								})}
							</span>
							{!collapsed && <span className={`ml-3 truncate ${item.name === 'Projects' ? 'font-bold tracking-wide text-base' : ''}`}>{item.name}</span>}
						</NavLink>
						</li>
					))}
				</ul>
			</nav>
			<div className="p-2 border-t border-gray-200 dark:border-gray-800">
				<button
					onClick={() => setCollapsed(!collapsed)}
					className="w-full p-2 rounded-md text-gray-500 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex items-center justify-center"
				>
					<svg
						className={`h-5 w-5 transition-transform ${collapsed ? 'rotate-180' : ''}`}
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							strokeLinecap="round"
							strokeLinejoin="round"
							strokeWidth={2}
							d={collapsed ? 'M13 5l7 7-7 7' : 'M11 19l-7-7 7-7'}
						/>
					</svg>
				</button>
			</div>
		</aside>
	);
};

export default Sidebar;