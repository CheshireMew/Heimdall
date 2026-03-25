import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'

const service: AxiosInstance = axios.create({
    baseURL: '/api/v1',
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Request Interceptor
service.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        return config
    },
    (error: unknown) => {
        return Promise.reject(error)
    }
)

// Response Interceptor
service.interceptors.response.use(
    (response: AxiosResponse) => {
        return response
    },
    (error: unknown) => {
        console.error('API Request Failed:', error)
        return Promise.reject(error)
    }
)

export default service
